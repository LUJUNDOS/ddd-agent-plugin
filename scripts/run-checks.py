#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run-checks.py —— 一键全量检查（替代原 .vscode/tasks.json 的闸门任务）

按序执行并汇总：DDD 闸门链 / 任务勾选 / CHANGELOG / 镜像一致性 / 单元测试。
任一失败即停（exit 1），全部通过 exit 0。纯标准库，宿主无关。

用法：
  python scripts/run-checks.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHECKS = [
    ("ddd_gate: gates", ["python", "scripts/ddd_gate.py", "gates", "docs", "--strict"]),
    ("ddd_gate: check-tasks", ["python", "scripts/ddd_gate.py", "check-tasks", "docs"]),
    ("ddd_gate: check-changelog", ["python", "scripts/ddd_gate.py", "check-changelog", "docs"]),
    ("drift_check", ["python", "scripts/drift_check.py"]),
    ("tests", ["python", "tests/test_plugin.py"]),
]


def main():
    failed = []
    for label, cmd in CHECKS:
        print(f"--- {label} ---")
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode != 0:
            failed.append(label)
    if failed:
        print(f"\n# run-checks: FAIL ✗（{', '.join(failed)}）")
        sys.exit(1)
    print("\n# run-checks: 全量检查通过 ✓")
    sys.exit(0)


if __name__ == "__main__":
    main()
