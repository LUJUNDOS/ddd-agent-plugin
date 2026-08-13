#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install.py —— 一键安装插件到目标宿主（03-design §7 / FR-006）

流程：generate（确保 dist 最新）→ 快照宿主既有 skill 文件 → 复制镜像 →
备份被覆盖文件 → 写 manifest-installed.json（卸载依据）。
幂等：重复 install 覆盖更新。

用法：
  python scripts/install.py --host <name> --target <宿主项目根>
"""
import argparse
import hashlib
import json
import os
import shutil
import sys

import generate

ROOT = generate.ROOT
MANIFEST_PREFIX = ".ddd-agent-plugin-manifest"
BACKUP_DIR = ".ddd-agent-plugin-backup"


def manifest_name(host):
    return f"{MANIFEST_PREFIX}-{host}.json"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot(base_dir):
    """扫描目录，返回 {相对路径: sha256}。目录不存在返回 {}。"""
    snap = {}
    if not os.path.isdir(base_dir):
        return snap
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if BACKUP_DIR in dirnames:
            dirnames.remove(BACKUP_DIR)
        # 排除所有本插件清单变体（manifest 在宿主根，不在 skills 下；此处兜底）
        filenames = [fn for fn in filenames if not fn.startswith(MANIFEST_PREFIX)]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            snap[os.path.relpath(fp, base_dir).replace("\\", "/")] = _sha256(fp)
    return snap


def _copy_tree_with_backup(src, dst, backup_dir, prefix=""):
    """复制 src 树到 dst，覆盖前备份原文件到 backup_dir。
    copied/backed_up 记录相对 target（dst 的父上下文）的完整路径（prefix 为顶层目录名）。"""
    copied, backed_up = [], []
    for dirpath, dirnames, filenames in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        target_dir = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target_dir, exist_ok=True)
        for fn in filenames:
            sp = os.path.join(dirpath, fn)
            tp = os.path.join(target_dir, fn)
            relp = os.path.relpath(tp, dst).replace("\\", "/")
            relp_full = (prefix + "/" + relp) if prefix else relp
            if os.path.isfile(tp):
                bdir = os.path.join(backup_dir, os.path.dirname(relp_full))
                os.makedirs(bdir, exist_ok=True)
                shutil.copy2(tp, os.path.join(bdir, fn))
                backed_up.append(relp_full)
            shutil.copy2(sp, tp)
            copied.append(relp_full)
    return copied, backed_up


def main(argv=None):
    ap = argparse.ArgumentParser(description="安装插件到目标宿主")
    ap.add_argument("--host", required=True, help="reasonix|claude")
    ap.add_argument("--target", required=True, help="宿主项目根目录")
    args = ap.parse_args(argv)

    manifest = generate.load_manifest()
    if args.host not in manifest["hosts"]:
        print(f"[FAIL] 未知宿主: {args.host}")
        sys.exit(1)
    host_cfg = manifest["hosts"][args.host]
    if not host_cfg.get("layout"):
        print(f"[FAIL] 宿主 {args.host} 未适配（planned）")
        sys.exit(1)

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print(f"[FAIL] 目标目录不存在: {target}")
        sys.exit(1)

    # 1) 生成最新镜像
    generate.generate_host(manifest, args.host, os.path.join(ROOT, "dist"))
    src = os.path.join(ROOT, "dist", args.host)

    # 2) 快照宿主既有 skill 文件
    with open(os.path.join(src, "layout.json"), encoding="utf-8") as f:
        layout = json.load(f)
    base_dir = os.path.join(target, layout["base_dir"].strip("/"))
    snapshot = _snapshot(base_dir)

    # 3) 复制（跳过 layout.json 元数据；保留顶层目录名如 .reasonix）
    backup_dir = os.path.join(target, BACKUP_DIR)
    shutil.rmtree(backup_dir, ignore_errors=True)
    copied, backed_up = [], []
    for entry in os.listdir(src):
        if entry == "layout.json":
            continue
        sp = os.path.join(src, entry)
        tp = os.path.join(target, entry)
        if os.path.isdir(sp):
            c, b = _copy_tree_with_backup(sp, tp, backup_dir, prefix=entry)
            copied.extend(c)
            backed_up.extend(b)
        else:
            relp = entry
            if os.path.isfile(tp):
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(tp, os.path.join(backup_dir, entry))
                backed_up.append(relp)
            shutil.copy2(sp, tp)
            copied.append(relp)

    # 4) 写安装清单（按宿主分文件，避免多宿主互相覆盖）
    installed = {
        "host": args.host,
        "base_dir": layout["base_dir"],
        "target": target,
        "files": sorted(copied),
        "backed_up": sorted(backed_up),
        "snapshot": snapshot,
        "installed_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }
    mpath = os.path.join(target, manifest_name(args.host))
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(installed, f, ensure_ascii=False, indent=2)

    print(f"install: {args.host} -> {target}")
    print(f"  files: {len(copied)}，backed_up: {len(backed_up)}")
    print(f"  manifest: {os.path.basename(mpath)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
