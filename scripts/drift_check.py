#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drift_check.py —— 镜像一致性校验（03-design §8 / FR-003）

重新从单一源生成，与 dist/<host>/ 现有镜像逐文件对比。
退出码：0 = 一致；1 = 存在漂移（供 hook/CI 拦截）。

用法：
  python scripts/drift_check.py [--host <name|all>] [--out dist]
"""
import argparse
import filecmp
import os
import shutil
import sys
import tempfile

import generate  # 复用单一源生成逻辑（同目录）

ROOT = generate.ROOT


def compare_trees(left, right):
    """返回差异文件相对路径列表（left 为基准）。"""
    diffs = []
    for dirpath, dirnames, filenames in os.walk(left):
        rel = os.path.relpath(dirpath, left)
        other = os.path.join(right, rel)
        for fn in sorted(filenames):
            lp = os.path.join(dirpath, fn)
            rp = os.path.join(other, fn)
            if not os.path.isfile(rp) or not filecmp.cmp(lp, rp, shallow=False):
                diffs.append(os.path.relpath(lp, left))
    # right 侧多出的文件
    for dirpath, dirnames, filenames in os.walk(right):
        rel = os.path.relpath(dirpath, right)
        other = os.path.join(left, rel)
        for fn in sorted(filenames):
            lp = os.path.join(other, fn)
            if not os.path.isfile(lp):
                diffs.append(f"[extra] {os.path.join(rel, fn)}")
    return diffs


def check_host(manifest, host, out_dir):
    tmp = tempfile.mkdtemp(prefix="drift-")
    try:
        generate.generate_host(manifest, host, tmp)
        # 重新生成的镜像根（generate 输出 tmp/<host>/ 结构与 dist/<host>/ 对齐）
        fresh = os.path.join(tmp, host)
        current = os.path.join(out_dir, host)
        if not os.path.isdir(current):
            return [f"[missing] {host} 镜像不存在，请先运行 generate.py"]
        diffs = compare_trees(fresh, current)
        return [f"{host}: {d}" for d in diffs]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="镜像一致性校验")
    ap.add_argument("--host", default="all", help="reasonix|claude|all（默认 all）")
    ap.add_argument("--out", default="dist", help="镜像目录（默认 dist）")
    args = ap.parse_args()

    manifest = generate.load_manifest()
    host_names = [h for h, c in manifest["hosts"].items() if c.get("layout")]
    if args.host != "all":
        if args.host not in manifest["hosts"]:
            print(f"[FAIL] 未知宿主: {args.host}")
            sys.exit(1)
        host_names = [args.host]
    out_dir = os.path.join(ROOT, args.out)

    all_diffs = []
    for host in host_names:
        all_diffs.extend(check_host(manifest, host, out_dir))

    if all_diffs:
        print(f"# drift_check: {len(all_diffs)} 处漂移 ✗")
        for d in all_diffs:
            print(f"  [DIFF] {d}")
        sys.exit(1)
    print(f"# drift_check: {host_names} 一致 ✓（0 差异）")
    sys.exit(0)


if __name__ == "__main__":
    main()
