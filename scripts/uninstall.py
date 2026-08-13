#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uninstall.py —— 一键卸载插件（03-design §7 / FR-007 / AC-5）

读 .ddd-agent-plugin-manifest.json → 删除插件文件 → 恢复被覆盖文件 →
删除 manifest 与 backup → 校验宿主 skill 目录与安装前快照一致。

用法：
  python scripts/uninstall.py --host <name> --target <宿主项目根>
退出码：0 = 卸载并校验通过；1 = 无 manifest 或校验失败（拒绝执行/报错）。
"""
import argparse
import json
import os
import shutil
import sys

import install

MANIFEST_NAME = install.MANIFEST_NAME
BACKUP_DIR = install.BACKUP_DIR


def main(argv=None):
    ap = argparse.ArgumentParser(description="卸载插件（恢复宿主原状）")
    ap.add_argument("--host", required=True, help="reasonix|claude")
    ap.add_argument("--target", required=True, help="宿主项目根目录")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    mpath = os.path.join(target, MANIFEST_NAME)
    if not os.path.isfile(mpath):
        print(f"[FAIL] 未找到安装清单 {MANIFEST_NAME}（拒绝卸载）")
        sys.exit(1)
    with open(mpath, "r", encoding="utf-8") as f:
        record = json.load(f)
    if record["host"] != args.host:
        print(f"[FAIL] 清单宿主 {record['host']} 与参数 {args.host} 不符")
        sys.exit(1)

    # 1) 删除插件文件（仅删清单记录的）
    deleted, missing = [], []
    for relp in record["files"]:
        fp = os.path.join(target, relp)
        if os.path.isfile(fp):
            os.remove(fp)
            deleted.append(relp)
        else:
            missing.append(relp)

    # 2) 恢复被覆盖文件
    backup_dir = os.path.join(target, BACKUP_DIR)
    restored = []
    for relp in record["backed_up"]:
        bp = os.path.join(backup_dir, relp)
        if os.path.isfile(bp):
            dp = os.path.join(target, relp)
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.copy2(bp, dp)
            restored.append(relp)

    # 3) 清理空目录 + manifest + backup
    for dirpath, dirnames, filenames in os.walk(target, topdown=False):
        if not dirnames and not filenames and dirpath != target:
            try:
                os.rmdir(dirpath)
            except OSError:
                pass
    os.remove(mpath)
    shutil.rmtree(backup_dir, ignore_errors=True)

    # 4) 校验：宿主 skill 目录与安装前快照一致（AC-5）
    base_dir = os.path.join(target, record["base_dir"].strip("/"))
    now = install._snapshot(base_dir)
    diff = []
    for k in set(record["snapshot"]) | set(now):
        if record["snapshot"].get(k) != now.get(k):
            diff.append(k)
    if diff:
        print(f"[FAIL] 卸载后目录与安装前快照不一致: {diff[:10]}")
        sys.exit(1)

    print(f"uninstall: {args.host} <- {target}")
    print(f"  deleted: {len(deleted)}，missing(已不存在): {len(missing)}，restored: {len(restored)}")
    print(f"  快照校验通过 ✓（宿主 skill 目录已恢复原状）")
    sys.exit(0)


if __name__ == "__main__":
    main()
