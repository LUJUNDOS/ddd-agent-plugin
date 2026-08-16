#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claude_gate_hook.py —— Claude Code PreToolUse 钩子（写文件前硬拦 DDD 闸门）

Claude Code 在 Edit/Write/NotebookEdit 前以 JSON 注入 stdin：
  {"tool_name": "Write", "tool_input": {"file_path": "...", "new_string": "..."}}
- 退出 0 = 放行；退出 2 = 拦截（Claude Code 据此拒绝落笔）。

逻辑复用 ddd_gate 的判定：
  - 改动 src/ 生产码 → 03-design 必须 approved
  - 改动下游 docs 文档试图放行 → 上游必须 approved
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ddd_gate as G


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # 解析失败不拦（fail-open，避免卡死）
    tool_input = data.get("tool_input", {})
    # 兼容两种宿主注入格式：Claude Code 用 file_path，Reasonix 用 path
    path = tool_input.get("file_path", "") or tool_input.get("path", "")
    if not path:
        sys.exit(0)

    # 定位 docs_dir：路径含 /docs/ → 取其父目录；否则向上找
    p = path.replace("\\", "/")
    docs_dir = None
    if "/docs/" in p:
        docs_dir = p[: p.index("/docs/") + len("/docs/")]
    else:
        cur = os.path.dirname(path)
        for _ in range(6):
            if os.path.isdir(os.path.join(cur, "docs")):
                docs_dir = os.path.join(cur, "docs")
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent

    if not docs_dir or not os.path.isdir(docs_dir):
        sys.exit(0)

    # src 改动 → 03-design 须 approved
    if "/src/" in p or p.startswith("src/"):
        ok, msgs = G.check_module(docs_dir, p)
        if not ok:
            sys.stderr.write("\n".join(msgs))
            sys.exit(2)
    # docs 下游文档放行 → 上游须 approved
    elif "/docs/" in p:
        base = os.path.basename(p)
        lvl = G.doc_level(base)
        if lvl and lvl > 0:
            docs = G.collect_docs(docs_dir)
            up = docs.get(lvl - 1)
            cur_doc = docs.get(lvl)
            # 仅当该文档当前已是/将要是 released 态才检查上游
            if cur_doc and cur_doc[1] in G.RELEASED and (up is None or up[1] != "approved"):
                sys.stderr.write(f"[BLOCK] {base} 已 {cur_doc[1]} 但上游 {G.CHAIN[lvl-1]} 未 approved")
                sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
