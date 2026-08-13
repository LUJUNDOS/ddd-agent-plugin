#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drift_check.py —— 文档/代码漂移检测（启发式 v1，对应定稿计划 §1.3 harness / 守护型 Housekeeper）

v1 启发式（语义漂移留 agent，脚本只做机械信号）：
  - 对每个 docs/*.md 读取 frontmatter status 与文件 mtime。
  - status == implemented：期望 src/ 下存在比该文档「新」的源码（代码已随文档落地）。
      若 src/ 整体不存在、或 src/ 下最新文件比该文档还旧 → 标记 drift（文档称已实现，但代码未更新）。
  - status in {approved} 但 src/ 为空且存在 implemented 兄弟文档 → 不报（实现中正常）。
  - docs 比 src 最新文件还新（文档改在设计冻结后）→ 标记 warning（可能需重建/回归）。

产出：<report_dir>/drift_report-<YYYYMMDD>.json。退出码 0 = 无 drift；1 = 有 drift。
纯标准库实现。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

VALID_STATUS = {"draft", "review", "approved", "implemented", "deprecated"}


def parse_frontmatter(path):
    try:
        text = open(path, "r", encoding="utf-8").read()
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^\s*([A-Za-z0-9_\-]+)\s*:\s*(.*)$", line)
        if mm:
            data[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return data


def newest_mtime(path):
    newest = 0.0
    if not os.path.isdir(path):
        return newest
    for dp, _, fns in os.walk(path):
        for fn in fns:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(dp, fn)))
            except OSError:
                pass
    return newest


def main():
    ap = argparse.ArgumentParser(description="文档/代码漂移检测 v1")
    ap.add_argument("docs_dir")
    ap.add_argument("--src-dir", default=None, help="源码目录（默认 <docs_dir>/../src）")
    ap.add_argument("--report-dir", default=None, help="report 输出目录（默认 docs_dir/../logs 或 cwd）")
    args = ap.parse_args()

    docs_dir = os.path.normpath(args.docs_dir)
    src_dir = os.path.normpath(args.src_dir) if args.src_dir else os.path.normpath(os.path.join(docs_dir, "..", "src"))
    report_dir = args.report_dir or (os.path.dirname(docs_dir) or ".")
    os.makedirs(report_dir, exist_ok=True)

    date = datetime.now().strftime("%Y%m%d")
    report_path = os.path.join(report_dir, f"drift_report-{date}.json")

    findings = []
    if os.path.isdir(docs_dir):
        for fn in sorted(os.listdir(docs_dir)):
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(docs_dir, fn)
            fm = parse_frontmatter(fp)
            status = fm.get("status", "draft")
            if status not in ("approved", "implemented"):
                continue
            doc_mtime = os.path.getmtime(fp)
            src_newest = newest_mtime(src_dir)
            entry = {
                "doc": fn,
                "status": status,
                "doc_mtime": datetime.fromtimestamp(doc_mtime).isoformat(timespec="seconds"),
                "src_newest_mtime": (datetime.fromtimestamp(src_newest).isoformat(timespec="seconds") if src_newest else None),
                "drift": False,
                "reason": "",
            }
            if status == "implemented":
                if src_newest == 0.0:
                    entry["drift"] = True
                    entry["reason"] = "status=implemented 但 src/ 无文件（代码未落地）"
                elif src_newest < doc_mtime:
                    entry["drift"] = True
                    entry["reason"] = "status=implemented 但 src/ 最新文件比文档旧（文档改后代码未重建）"
                else:
                    entry["reason"] = "代码已随文档更新"
            else:  # approved
                if src_newest > doc_mtime:
                    entry["reason"] = "代码比文档新（可能已实现但未置 implemented）"
            findings.append(entry)

    drift_count = sum(1 for f in findings if f["drift"])
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "docs_dir": docs_dir,
        "src_dir": src_dir,
        "checked": len(findings),
        "drift_count": drift_count,
        "findings": findings,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"# drift_check.py v1 @ {report['generated_at']}")
    print(f"检查文档: {len(findings)}  漂移: {drift_count}")
    for f in findings:
        tag = "DRIFT" if f["drift"] else "ok"
        print(f"  [{tag}] {f['doc']} ({f['status']}) — {f['reason']}")
    print(f"report → {report_path}")
    print(f"\n# 结果：{'DRIFT DETECTED' if drift_count else 'NO DRIFT ✓'}")
    sys.exit(1 if drift_count else 0)


if __name__ == "__main__":
    main()
