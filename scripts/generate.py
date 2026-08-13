#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py —— 从单一源生成各宿主镜像（03-design §4 / AD-0001）

读 plugin.manifest.yaml × templates/*.md × hosts/<host>/layout.json，
渲染 dist/<host>/ 完整镜像（skills 目录树 + scripts 拷贝 + layout 元数据）。
纯标准库实现（string.Template），无第三方依赖（NFR-01）。

用法：
  python scripts/generate.py [--host <name|all>] [--out dist]
退出码：0 = 成功；1 = 失败（manifest 解析 / 模板缺失 / 宿主未声明）。
"""
import argparse
import json
import os
import re
import shutil
import string
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)


# ---------- 极简 YAML 子集解析（仅支持本 manifest 用到的结构） ----------

def _scalar(v):
    v = v.strip()
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if v in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_yaml_subset(text):
    """解析：注释 / 嵌套 mapping / `- key: val` 列表项 / `- val` 列表项。
    非本项目用到的 YAML 特性会抛 ValueError（fail-fast，宁缺毋滥）。"""
    lines = [ln for ln in text.splitlines()
             if ln.strip() and not ln.strip().startswith("#")]
    root = {}
    stack = [(-1, root)]      # (indent, dict)
    list_stack = []           # (indent, list)
    i = 0
    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip())
        content = line.strip()
        if content.startswith("- "):
            rest = content[2:].strip()
            while list_stack and list_stack[-1][0] >= indent:
                list_stack.pop()
            if not list_stack:
                raise ValueError(f"列表项无容器: {line}")
            lst = list_stack[-1][1]
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", rest)
            if m:
                item = {}
                lst.append(item)
                item[m.group(1)] = _scalar(m.group(2))
                stack.append((indent, item))
            else:
                lst.append(_scalar(rest))
        else:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", content)
            if not m:
                raise ValueError(f"无法解析: {line}")
            key, val = m.group(1), m.group(2).strip()
            while stack and stack[-1][0] >= indent:
                stack.pop()
            cur = stack[-1][1]
            if val == "":
                if i + 1 < len(lines):
                    nxt = lines[i + 1]
                    nindent = len(nxt) - len(nxt.lstrip())
                    ncontent = nxt.strip()
                    if ncontent.startswith("- "):
                        new_list = []
                        cur[key] = new_list
                        list_stack.append((indent, new_list))
                    elif nindent > indent:
                        new_dict = {}
                        cur[key] = new_dict
                        stack.append((indent, new_dict))
                    else:
                        cur[key] = None
                else:
                    cur[key] = None
            elif val.startswith("[") and val.endswith("]"):
                cur[key] = json.loads(val)
            else:
                cur[key] = _scalar(val)
        i += 1
    return root


# ---------- 生成 ----------

def load_manifest():
    path = os.path.join(ROOT, "plugin.manifest.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return parse_yaml_subset(f.read())


def render_skill(tpl_path, skill):
    with open(tpl_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    # 03-design §4：{{SKILL_NAME}}/{{SKILL_DESC}} 占位符（string.Template 不认 {{}}，用显式替换）
    return (tpl
            .replace("{{SKILL_NAME}}", skill["id"])
            .replace("{{SKILL_DESC}}", skill["description"]))


def generate_host(manifest, host, out_dir):
    host_cfg = manifest["hosts"][host]
    layout_path = host_cfg.get("layout")
    if not layout_path:
        raise ValueError(f"宿主 {host} 未声明 layout（planned 状态，未适配）")
    with open(os.path.join(ROOT, layout_path), "r", encoding="utf-8") as f:
        layout = json.load(f)
    base = os.path.join(out_dir, host)
    base_dir = layout["base_dir"].strip("/")
    for skill in manifest["skills"]:
        skill_dir = layout["skill_dir"].replace("<skill-id>", skill["id"])
        dest = os.path.join(base, base_dir, skill_dir)
        os.makedirs(dest, exist_ok=True)
        body = render_skill(
            os.path.join(ROOT, "templates", skill["id"] + ".md"), skill)
        with open(os.path.join(dest, layout["skill_file"]), "w", encoding="utf-8") as f:
            f.write(body)
    # 拷贝随插件分发的脚本
    scripts_out = os.path.join(base, "scripts")
    os.makedirs(scripts_out, exist_ok=True)
    for s in manifest.get("scripts", []):
        src = os.path.join(ROOT, s)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(scripts_out, os.path.basename(s)))
    # 拷贝 references（角色 skill 的方法论依赖，03-design §13）
    refs_out = os.path.join(base, "references")
    for r in manifest.get("references", []):
        src = os.path.join(ROOT, r)
        if os.path.isfile(src):
            os.makedirs(refs_out, exist_ok=True)
            shutil.copy2(src, os.path.join(refs_out, os.path.basename(r)))
    # layout 元数据（install 用；不进宿主）
    with open(os.path.join(base, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f, ensure_ascii=False, indent=2)
    return base


def main():
    ap = argparse.ArgumentParser(description="生成各宿主镜像（单一源）")
    ap.add_argument("--host", default="all", help="reasonix|claude|all（默认 all）")
    ap.add_argument("--out", default="dist", help="输出目录（默认 dist）")
    args = ap.parse_args()

    manifest = load_manifest()
    host_names = [h for h, c in manifest["hosts"].items() if c.get("layout")]
    if args.host != "all":
        if args.host not in manifest["hosts"]:
            print(f"[FAIL] 未知宿主: {args.host}（可用: {list(manifest['hosts'])}）")
            sys.exit(1)
        host_names = [args.host]
    out_dir = os.path.join(ROOT, args.out)
    os.makedirs(out_dir, exist_ok=True)
    produced = []
    for host in host_names:
        produced.append(generate_host(manifest, host, out_dir))
    print(f"generate: {host_names} -> {os.path.abspath(out_dir)}")
    for p in produced:
        print(f"  {os.path.relpath(p, ROOT)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
