#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ddd_gate.py —— DDD 四道闸门机械校验器（harness 硬约束，不依赖 AI 自觉）

设计目标（对应定稿计划 §1.3 Harness 三层强制之「机械层」）：
  读各 docs/*.md 的 frontmatter `status`，静态校验「上游 approved 才放行下游」：
    - 00-vision → 01-requirements → 02-architecture → 03-design → 04-tasks
    - 下游文档不得在上游未 approved 时进入 approved/implemented
    - 写 src/ 生产码前，对应模块所属的 03-design 必须 approved（pre-commit 模式）
    - gates --strict：G0 硬闸门，00/01 未 approved 直接 FAIL（防 AI 绕过开始实现）

退出码：0 = 全部通过；1 = 存在闸门违规（供 pre-commit / CI / VS Code 任务拦截）。
纯标准库实现，无第三方依赖，可直接被 Bash / GitHub Actions / pre-commit 调用。

用法：
  python ddd_gate.py gates <docs_dir> [--strict]
  python ddd_gate.py pre-commit <docs_dir> --changed <f1> [<f2> ...]
  python ddd_gate.py check-module <docs_dir> --module <src/path>
  python ddd_gate.py check-changelog <docs_dir>
  python ddd_gate.py check-tasks <docs_dir>

兼容 Windows 路径（正斜杠/反斜杠均可）。
"""
import argparse
import os
import re
import sys
from datetime import datetime

# DDD 事实链顺序（按文件名前缀判定层级）
CHAIN = ["00-vision", "01-requirements", "02-architecture", "03-design", "04-tasks"]
# status 合法取值
VALID_STATUS = {"draft", "review", "approved", "implemented", "deprecated"}

# 下游可以进入的「放行态」
RELEASED = {"approved", "implemented"}


def parse_frontmatter(path):
    """极简 frontmatter 解析：返回 dict。仅支持 `key: value` 顶层行。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    data = {}
    for line in block.splitlines():
        mm = re.match(r"^\s*([A-Za-z0-9_\-]+)\s*:\s*(.*)$", line)
        if mm:
            key = mm.group(1)
            val = mm.group(2).strip().strip('"').strip("'")
            data[key] = val
    return data


def doc_level(filename):
    """从文件名推断 DDD 层级索引；非 DDD 文档返回 None。"""
    base = os.path.basename(filename)
    for i, prefix in enumerate(CHAIN):
        if base.startswith(prefix):
            return i
    return None


def collect_docs(docs_dir):
    """扫描 docs_dir，返回 {level_index: (path, status)}（每层级取第一个匹配文件）。"""
    found = {}
    if not os.path.isdir(docs_dir):
        return found
    for fn in sorted(os.listdir(docs_dir)):
        if not fn.endswith(".md"):
            continue
        lvl = doc_level(fn)
        if lvl is None:
            continue
        fm = parse_frontmatter(os.path.join(docs_dir, fn))
        status = fm.get("status", "draft")
        if lvl not in found:
            found[lvl] = (os.path.join(docs_dir, fn), status)
    return found


def check_changelog(docs_dir):
    """检查所有 DDD 文档是否在 CHANGELOG.md 中有变更记录。

    规则：对每个存在的 DDD 文档（00-04），若其文件修改时间晚于 CHANGELOG.md
    的修改时间，则认为"文档已修改但 CHANGELOG 未更新"→ 违规。

    返回 (passed: bool, messages: list)。
    """
    msgs = []
    changelog_path = os.path.join(docs_dir, "CHANGELOG.md")

    if not os.path.isfile(changelog_path):
        msgs.append("[INFO] CHANGELOG.md 不存在，跳过 CHANGELOG 一致性检查")
        return True, msgs

    changelog_mtime = os.path.getmtime(changelog_path)

    violated = []
    for prefix in CHAIN:
        doc_path = os.path.join(docs_dir, f"{prefix}.md")
        if not os.path.isfile(doc_path):
            continue
        doc_mtime = os.path.getmtime(doc_path)
        if doc_mtime > changelog_mtime:
            violated.append(prefix)
            msgs.append(
                f"[CHANGELOG] {prefix}.md 已修改但 CHANGELOG.md 未更新"
                f"（doc mtime: {datetime.fromtimestamp(doc_mtime).strftime('%Y-%m-%d %H:%M')}"
                f"，CHANGELOG mtime: {datetime.fromtimestamp(changelog_mtime).strftime('%Y-%m-%d %H:%M')}）→ 违规"
            )

    if violated:
        msgs.append(
            f"[CHANGELOG] 共 {len(violated)} 个文档修改后未记录变更："
            f"{', '.join(violated)} → 请追加 docs/CHANGELOG.md 条目后重试"
        )
        return False, msgs

    msgs.append("[OK]   CHANGELOG：所有 DDD 文档变更已记录 ✓")
    return True, msgs


def check_tasks(docs_dir):
    """检查 04-tasks.md 中未勾选的 TASK 是否已有验证证据。

    规则：扫 04-tasks.md 中所有 [ ] TASK-NNN，在以下位置搜索验证证据：
      - <project>/validations/ 目录（文件内容含 TASK ID）
      - <project>/contracts/C-*.md（仅 status=done 的契约，文件内容含 TASK ID）
      - <project>/tasks/logs/ 目录（文件内容含 TASK ID）
    有证据但 [ ] 未勾选 → WARNING（不 BLOCK，不改变退出码）。

    返回 (passed: bool, messages: list)。passed 始终 True（WARNING 级）。
    """
    msgs = []
    tasks_path = os.path.join(docs_dir, "04-tasks.md")

    if not os.path.isfile(tasks_path):
        msgs.append("[INFO] 04-tasks.md 不存在，跳过 task 勾选检查")
        return True, msgs

    # 提取所有未勾选的 TASK-NNN
    try:
        with open(tasks_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        msgs.append("[INFO] 04-tasks.md 读取失败，跳过 task 勾选检查")
        return True, msgs

    # 匹配 - [ ] **TASK-NNN** （未勾选）
    unchecked = re.findall(r"^\s*- \[ \] \*\*(TASK-[A-Z0-9\-]+)\*\*", content, re.MULTILINE)
    if not unchecked:
        msgs.append("[OK]   check-tasks：所有 TASK 已勾选或无 TASK 需检查 ✓")
        return True, msgs

    # 项目根目录 = docs_dir 的上级
    project_dir = os.path.dirname(os.path.abspath(docs_dir))

    # 收集验证证据：在 validations/、contracts/C-*.md、tasks/logs/ 中搜 TASK ID
    evidence_dirs = [
        os.path.join(project_dir, "validations"),
        os.path.join(project_dir, "tasks", "logs"),
    ]
    contracts_dir = os.path.join(project_dir, "contracts")

    # 搜索函数：在目录中扫所有文件，返回包含 task_id 的文件列表
    def _search_evidence(task_id):
        hits = []
        for search_dir in evidence_dirs:
            if not os.path.isdir(search_dir):
                continue
            for fn in sorted(os.listdir(search_dir)):
                fpath = os.path.join(search_dir, fn)
                if not os.path.isfile(fpath):
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                except OSError:
                    continue
                if task_id in text:
                    rel = os.path.relpath(fpath, project_dir)
                    hits.append(rel)
        # 契约目录特殊处理：仅 status=done 的契约才算证据
        if os.path.isdir(contracts_dir):
            for fn in sorted(os.listdir(contracts_dir)):
                if not fn.startswith("C-") or not fn.endswith(".md"):
                    continue
                fpath = os.path.join(contracts_dir, fn)
                if not os.path.isfile(fpath):
                    continue
                fm = parse_frontmatter(fpath)
                if fm.get("status") != "done":
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                except OSError:
                    continue
                if task_id in text:
                    rel = os.path.relpath(fpath, project_dir)
                    hits.append(rel)
        return hits

    warnings = []
    for task_id in unchecked:
        hits = _search_evidence(task_id)
        if hits:
            warnings.append((task_id, hits))

    if warnings:
        msgs.append(
            f"[WARN] check-tasks：{len(warnings)} 个 TASK 有验证证据但未勾选 [x]："
        )
        for task_id, hits in warnings:
            hit_str = ", ".join(hits[:3])
            if len(hits) > 3:
                hit_str += f" 等 {len(hits)} 个文件"
            msgs.append(f"  {task_id} ← 证据：{hit_str}")
        msgs.append(
            "  → 请确认验证已通过后，将 04-tasks.md 中对应 TASK 勾选为 [x]"
        )
    else:
        msgs.append(
            f"[OK]   check-tasks：{len(unchecked)} 个未勾选 TASK，均无验证证据（未实现或未验证）✓"
        )

    return True, msgs  # 始终 True（WARNING 级，不改变退出码）


def check_gates(docs_dir, strict=False):
    """校验整条 DDD 闸门链。返回 (passed: bool, messages: list)。"""
    msgs = []
    docs = collect_docs(docs_dir)
    passed = True

    # 检查每个下游层级：其上游必须 approved
    for i in range(1, len(CHAIN)):
        cur = docs.get(i)
        if cur is None:
            continue
        path, status = cur
        if status not in RELEASED:
            continue  # 还没放行，不违反
        # 上游必须 approved
        upstream = docs.get(i - 1)
        if upstream is None:
            msgs.append(f"[GATE] {CHAIN[i]} 已 {status}，但上游 {CHAIN[i-1]} 缺失 → 违规")
            passed = False
            continue
        up_path, up_status = upstream
        if up_status != "approved":
            msgs.append(
                f"[GATE] {CHAIN[i]} 已 {status}，但上游 {CHAIN[i-1]} 状态为 "
                f"'{up_status}'（需 approved）→ 违规"
            )
            passed = False
        else:
            msgs.append(f"[OK]   {CHAIN[i]} ({status}) ← 上游 {CHAIN[i-1]} approved ✓")

    # 未出现的高层文档提示（非违规）
    for i, prefix in enumerate(CHAIN):
        if i not in docs:
            msgs.append(f"[INFO] {prefix} 文档缺失（尚未创建，不违规）")

    if strict:
        # strict 模式：G0 硬闸门 —— 00/01 必须存在且 approved，否则禁止开始实现
        v_doc = docs.get(0)
        if v_doc is None:
            msgs.append("[GATE] G0 未通过：缺少 00-vision（立项文档）→ 禁止开始实现")
            passed = False
        else:
            v_path, v_status = v_doc
            if v_status != "approved":
                msgs.append(
                    f"[GATE] G0 未通过：00-vision 状态为 '{v_status}'（需 approved）"
                    f" → 禁止写 02-architecture 或开始实现。请先 /goal 批准。"
                )
                passed = False
            else:
                msgs.append(f"[OK]   G0: 00-vision approved ✓")

        r_doc = docs.get(1)
        if r_doc is None:
            msgs.append("[GATE] G0 未通过：缺少 01-requirements（需求文档）→ 禁止开始实现")
            passed = False
        else:
            r_path, r_status = r_doc
            if r_status != "approved":
                msgs.append(
                    f"[GATE] G0 未通过：01-requirements 状态为 '{r_status}'（需 approved）"
                    f" → 禁止写 02-architecture 或开始实现。请先 /goal 批准。"
                )
                passed = False
            else:
                msgs.append(f"[OK]   G0: 01-requirements approved ✓")

        # strict 模式额外检查：CHANGELOG 一致性
        cl_passed, cl_msgs = check_changelog(docs_dir)
        msgs.extend(cl_msgs)
        if not cl_passed:
            passed = False

        # strict 模式额外检查：TASK 勾选一致性（WARNING 级，不影响 passed）
        _, task_msgs = check_tasks(docs_dir)
        msgs.extend(task_msgs)

    return passed, msgs


def check_precommit(docs_dir, changed):
    """pre-commit 拦截：给定本次改动文件，判定是否放行。"""
    msgs = []
    docs = collect_docs(docs_dir)
    blocked = False

    # 规则 A：改了 src/ 生产码 → 03-design 必须 approved
    def _is_src(p):
        p = p.replace("\\", "/")
        return ("/src/" in p) or p.startswith("src/") or p.startswith("src\\")
    src_changed = [c for c in changed if _is_src(c)]
    if src_changed:
        design = docs.get(3)
        if design is None or design[1] != "approved":
            msgs.append(
                f"[BLOCK] 改动生产码 {len(src_changed)} 个文件，但 03-design 未 approved"
                f"（当前：{design[1] if design else '缺失'}）→ 禁止落笔，请先走 G1 设计闸门"
            )
            blocked = True
        else:
            msgs.append("[OK]   生产码改动：03-design approved ✓")

    # 规则 B：改了下游设计文档但上游未 approved
    for c in changed:
        c = c.replace("\\", "/")
        if not (c.startswith("docs/") or "/docs/" in c):
            continue
        base = os.path.basename(c)
        lvl = doc_level(base)
        if lvl is None or lvl == 0:
            continue
        design_doc = docs.get(lvl)
        if design_doc is None:
            continue
        # 若该文档自身正要被改成 approved，需先确认上游
        upstream = docs.get(lvl - 1)
        if upstream is not None and upstream[1] != "approved":
            msgs.append(
                f"[BLOCK] docs/{base} 试图放行，但上游 {CHAIN[lvl-1]} 未 approved → 拦截"
            )
            blocked = True

    # 规则 C：docs/ 下的 DDD 文档有改动 → 必须更新 CHANGELOG
    norm_changed = [c.replace("\\", "/") for c in changed]
    docs_changed = [
        c for c in norm_changed
        if (c.startswith("docs/") or "/docs/" in c) and any(c.endswith(f"{p}.md") for p in CHAIN)
    ]
    if docs_changed:
        cl_passed, cl_msgs = check_changelog(docs_dir)
        msgs.extend(cl_msgs)
        if not cl_passed:
            blocked = True

    # 规则 D：DDD 文档有变更 → 提示检查 CLAUDE.md 纪律表述是否受影响（CodeBuddy 已退役，项目级只读 CLAUDE.md）
    if docs_changed:
        msgs.append(
            "[WARN] docs 变更——请同步检查 CLAUDE.md 的 §0 范围速览与角色职责"
            "表述是否受影响（规则 §1 纪律文档同步检查），受影响则修订"
        )

    # 规则 E：改了 src/ 或 docs/ → 检查 TASK 勾选一致性（WARNING 级，不 BLOCK）
    if src_changed or docs_changed:
        _, task_msgs = check_tasks(docs_dir)
        msgs.extend(task_msgs)

    if not blocked:
        msgs.append("[OK]   pre-commit：无闸门违规，放行")
    return (not blocked), msgs


def check_module(docs_dir, module_path):
    """检查某 src 模块对应的 03-design 是否已 approved（AI 写码前自检）。"""
    docs = collect_docs(docs_dir)
    design = docs.get(3)
    if design is None:
        return False, ["[FAIL] 03-design.md 缺失 → 禁止写码"]
    if design[1] != "approved":
        return False, [f"[FAIL] 03-design 状态 '{design[1]}'（需 approved）→ 禁止写 {module_path}"]
    return True, [f"[OK]   模块 {module_path}：03-design approved ✓，可写码"]


def main():
    ap = argparse.ArgumentParser(description="DDD 四道闸门机械校验器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gates", help="校验整条 DDD 闸门链")
    g.add_argument("docs_dir")
    g.add_argument("--strict", action="store_true", help="G0 硬闸门：要求 00/01 必须存在且 approved")

    p = sub.add_parser("pre-commit", help="pre-commit 拦截检查")
    p.add_argument("docs_dir")
    p.add_argument("--changed", nargs="+", required=True, help="本次改动的文件路径列表")

    c = sub.add_parser("check-module", help="检查某 src 模块设计是否已 approved")
    c.add_argument("docs_dir")
    c.add_argument("--module", required=True)

    cl = sub.add_parser("check-changelog", help="检查 DDD 文档变更是否均已记录 CHANGELOG")
    cl.add_argument("docs_dir")

    ct = sub.add_parser("check-tasks", help="检查未勾选 TASK 是否已有验证证据（WARNING 级）")
    ct.add_argument("docs_dir")

    args = ap.parse_args()
    print(f"# ddd_gate.py @ {datetime.now().isoformat(timespec='seconds')}")

    if args.cmd == "gates":
        passed, msgs = check_gates(args.docs_dir, args.strict)
    elif args.cmd == "pre-commit":
        passed, msgs = check_precommit(args.docs_dir, args.changed)
    elif args.cmd == "check-module":
        passed, msgs = check_module(args.docs_dir, args.module)
    elif args.cmd == "check-changelog":
        passed, msgs = check_changelog(args.docs_dir)
    elif args.cmd == "check-tasks":
        passed, msgs = check_tasks(args.docs_dir)
    else:
        ap.print_help()
        sys.exit(2)

    for m in msgs:
        print(m)
    print(f"\n# 结果：{'PASS ✓' if passed else 'FAIL ✗'}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
