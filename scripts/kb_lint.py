#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb_lint.py —— 知识库一致性清扫（对应定稿计划 §2.13 模板1 Docs Sweep / 守护型 loop）

检查项：
  1. 孤立页（orphan）：wiki/ 下某页从未被其他页引用、也未在 index.md 登记。
  2. 断链（broken link）：markdown 链接 / wiki 链接指向不存在的文件。
  3. 索引一致性（index diff）：wiki/index.md 登记条目 vs 实际 wiki 页集合的差异。
  4. raw/ 只读铁律校验：lint 只读取，绝不修改 raw/（此处仅 sanity 检查 raw 存在性）。

产出：kb/.lint/report-<YYYYMMDD>.json（供 agent 读取并修复；脚本不改写任何知识页）。
纯标准库实现。退出码：0 = 无问题；1 = 有问题（守护型 loop 据此决定是否派 agent 修复）。
"""
import argparse
import json
import os
import re
from datetime import datetime

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")          # [text](target)
WIKI_RE = re.compile(r"\[\[([^\]]+)\]\]")                # [[PageName]]


def find_md(root):
    out = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.endswith(".md"):
                out.append(os.path.join(dp, fn))
    return out


def resolve_target(src_file, target):
    """把链接 target 解析为绝对路径（支持相对路径与 wiki 页名）。"""
    target = target.strip()
    if target.startswith("http") or target.startswith("#"):
        return None
    # 相对路径
    cand = os.path.normpath(os.path.join(os.path.dirname(src_file), target))
    if os.path.exists(cand):
        return cand
    # wiki 页名：在 wiki/ 下找 <name>.md
    name = os.path.basename(target)
    name = re.sub(r"\.(md|markdown)$", "", name)
    wiki_root = os.path.join(os.path.dirname(src_file), "..", "wiki")
    wiki_root = os.path.normpath(wiki_root)
    if os.path.isdir(wiki_root):
        for dp, _, fns in os.walk(wiki_root):
            for fn in fns:
                if fn.endswith(".md") and re.sub(r"\.md$", "", fn) == name:
                    return os.path.join(dp, fn)
    return None  # 解析失败 = 可能断链


def main():
    ap = argparse.ArgumentParser(description="知识库 lint")
    ap.add_argument("kb_dir", help="kb/ 根目录")
    ap.add_argument("--report-dir", default=None, help="report 输出目录（默认 kb/.lint）")
    ap.add_argument("--pages", nargs="*", default=None, help="限定扫范围：只校验这些 wiki 页的相关链接（不填则全量扫）")
    args = ap.parse_args()

    kb_dir = os.path.normpath(args.kb_dir)
    wiki_dir = os.path.join(kb_dir, "wiki")
    raw_dir = os.path.join(kb_dir, "raw")
    index_file = os.path.join(wiki_dir, "index.md")
    report_dir = args.report_dir or os.path.join(kb_dir, ".lint")
    os.makedirs(report_dir, exist_ok=True)

    date = datetime.now().strftime("%Y%m%d")
    report_path = os.path.join(report_dir, f"report-{date}.json")

    wiki_pages = find_md(wiki_dir) if os.path.isdir(wiki_dir) else []
    raw_pages = find_md(raw_dir) if os.path.isdir(raw_dir) else []

    orphan_pages = []
    broken_links = []

    # 收集引用关系
    referenced = set()
    for page in wiki_pages:
        try:
            text = open(page, "r", encoding="utf-8").read()
        except OSError:
            continue
        for m in LINK_RE.finditer(text):
            tgt = resolve_target(page, m.group(1))
            if tgt:
                referenced.add(os.path.normpath(tgt))
            else:
                broken_links.append({"from": page, "link": m.group(1)})
        for m in WIKI_RE.finditer(text):
            tgt = resolve_target(page, m.group(1))
            if tgt:
                referenced.add(os.path.normpath(tgt))
            else:
                broken_links.append({"from": page, "link": f"[[{m.group(1)}]]"})

    # --pages 限定：规范化传入路径
    target_pages = None
    if args.pages:
        target_pages = set()
        for p in args.pages:
            # 支持传入相对于 kb_dir 的路径或绝对路径
            abs_p = os.path.normpath(p) if os.path.isabs(p) else os.path.normpath(os.path.join(kb_dir, p))
            if os.path.isfile(abs_p) and abs_p.endswith(".md"):
                target_pages.add(abs_p)
            elif os.path.isdir(abs_p):
                for fn in os.listdir(abs_p):
                    if fn.endswith(".md"):
                        target_pages.add(os.path.normpath(os.path.join(abs_p, fn)))

    # 孤立页：wiki 页不在 referenced 集合、也不在 index.md
    index_entries = set()
    if os.path.exists(index_file):
        idx_text = open(index_file, "r", encoding="utf-8").read()
        for m in LINK_RE.finditer(idx_text):
            tgt = resolve_target(index_file, m.group(1))
            if tgt:
                index_entries.add(os.path.normpath(tgt))
        for line in idx_text.splitlines():
            for wm in WIKI_RE.finditer(line):
                tgt = resolve_target(index_file, wm.group(1))
                if tgt:
                    index_entries.add(os.path.normpath(tgt))

    for page in wiki_pages:
        pn = os.path.normpath(page)
        base = os.path.basename(page)
        if base == "index.md":
            continue
        if pn not in referenced and pn not in index_entries:
            orphan_pages.append(page)

    # 索引一致性
    index_diff = {
        "in_index_not_exist": sorted(
            [p for p in index_entries if not os.path.exists(p)]
        ),
        "exist_not_in_index": sorted(
            [p for p in wiki_pages if os.path.normpath(p) not in index_entries and os.path.basename(p) != "index.md"]
        ),
    }

    # --pages 过滤：只保留与限定页相关的问题
    if target_pages is not None:
        broken_links = [
            bl for bl in broken_links
            if os.path.normpath(bl["from"]) in target_pages
        ]
        orphan_pages = [
            op for op in orphan_pages
            if os.path.normpath(op) in target_pages
        ]

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "kb_dir": kb_dir,
        "scope": "targeted" if target_pages is not None else "full",
        "target_pages": sorted(list(target_pages)) if target_pages else None,
        "wiki_page_count": len(wiki_pages),
        "raw_page_count": len(raw_pages),
        "orphan_pages": orphan_pages,
        "broken_links": broken_links,
        "index_diff": index_diff,
        "summary": {
            "orphan_count": len(orphan_pages),
            "broken_link_count": len(broken_links),
            "index_diff_count": len(index_diff["in_index_not_exist"]) + len(index_diff["exist_not_in_index"]),
        },
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"# kb_lint.py @ {report['generated_at']}")
    print(f"wiki 页: {report['wiki_page_count']}  raw 页: {report['raw_page_count']}")
    print(f"孤立页: {report['summary']['orphan_count']}")
    print(f"断链:   {report['summary']['broken_link_count']}")
    print(f"索引差异: {report['summary']['index_diff_count']}")
    print(f"report → {report_path}")

    has_issue = report["summary"]["orphan_count"] or report["summary"]["broken_link_count"] or report["summary"]["index_diff_count"]
    print(f"\n# 结果：{'ISSUES FOUND' if has_issue else 'CLEAN ✓'}")
    sys_exit_code = 0 if not has_issue else 1
    sys.exit(sys_exit_code)


if __name__ == "__main__":
    # 兼容直接运行
    import sys
    main()
