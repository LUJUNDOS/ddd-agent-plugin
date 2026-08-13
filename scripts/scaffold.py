#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scaffold.py —— 新建项目 DDD 文档骨架生成（03-design §14 / FR-014）

在目标项目生成 docs/00-vision.md ~ 04-tasks.md 空模板（frontmatter + 章节），
自动化代替手动初始化。幂等：已存在的文档跳过（报 INFO）。

用法：
  python scripts/scaffold.py --target <项目根>
退出码：0 = 成功；1 = 参数错误/目标不存在。
"""
import argparse
import os
import sys

DOCS = [
    ("00-vision", "00", [], """# 00-vision —— 项目愿景

## 1. 背景与问题

（为什么做这个项目？现状痛点是什么？）

## 2. 愿景

（一句话：项目要达成的状态）

## 3. 目标

| # | 目标 | 度量 |
|---|------|------|
| G1 |  |  |

## 4. 非目标（MVP 明确不做）

- 

## 5. 成功标准

（可自我证明的一句话）
"""),
    ("01-requirements", "01", ["00-vision"], """# 01-requirements —— SRS

> 依据 00-vision。每条需求标来源（V=用户亲口 / A=Agent 推断 / I=行业默认）与优先级（P0/P1）。

## 1. 功能需求（FR）

| ID | 需求 | 来源 | 优先级 |
|----|------|------|--------|
| FR-001 |  | V | P0 |

## 2. 非功能需求（NFR）

| ID | 需求 | 度量 |
|----|------|------|
| NFR-01 |  |  |

## 3. 验收标准（G3 对照）

| ID | 验收标准 | 验证方式 |
|----|---------|---------|
| AC-1 |  |  |

## 4. MVP 边界

- **不做**：

## 5. Ubiquitous Language

| 词 | 含义 |
|----|------|
|  |  |
"""),
    ("02-architecture", "02", ["00-vision", "01-requirements"], """# 02-architecture —— 架构

> 依据 01-requirements。上游 approved 后本层方可 approved。

## 1. 架构总览

（分层/模块图）

## 2. 组件职责

| 组件 | 职责 | 对应 FR |
|------|------|---------|
|  |  |  |

## 3. 关键架构决策（ADR）

### AD-0001 决策标题
- **背景**：
- **决策**：
- **后果**：

## 4. 复用举证表

| 组件 | 复用来源 | 复用部分 | 改造量 | 工作量估算 | 风险 |
|------|---------|---------|--------|-----------|------|
|  |  |  |  |  |  |
"""),
    ("03-design", "03", ["02-architecture"], """# 03-design —— 详细设计

> 依据 02-architecture。每模块实现前须本层 approved（G2 闸门）。

## 1. 模块设计

（每个模块：接口 / 数据结构 / 验收点）

## 2. 测试设计

| 用例 | 验证点 | 对应 AC |
|------|--------|---------|
| UT-1 |  |  |
"""),
    ("04-tasks", "04", ["03-design"], """# 04-tasks —— 任务拆分

> 依据 03-design（approved）。每任务可独立运行、独立验收。
> 勾选规则：实现+验证通过后改 [x]；check-tasks 核对 validations/tasks/logs 证据。

- [ ] **TASK-0001** 任务一
  - **内容**：
  - **DoD**：
"""),
]


def scaffold(target):
    docs_dir = os.path.join(target, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    created, skipped = [], []
    for name, layer, related, body in DOCS:
        path = os.path.join(docs_dir, f"{name}.md")
        if os.path.isfile(path):
            skipped.append(path)
            continue
        related_yaml = ", ".join(f"\"{r}\"" for r in related)
        frontmatter = (
            f"---\n"
            f"status: draft\n"
            f"title: {name}\n"
            f"layer: {layer}\n"
            f"related: [{related_yaml}]\n"
            f"---\n\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter + body)
        created.append(path)
    return created, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description="新建项目 DDD 文档骨架生成")
    ap.add_argument("--target", required=True, help="目标项目根目录")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print(f"[FAIL] 目标目录不存在: {target}")
        sys.exit(1)

    created, skipped = scaffold(target)
    for p in created:
        print(f"  created: {os.path.relpath(p, target)}")
    for p in skipped:
        print(f"  skipped(已存在): {os.path.relpath(p, target)}")
    print(f"scaffold: {len(created)} created, {len(skipped)} skipped -> {target}")
    sys.exit(0)


if __name__ == "__main__":
    main()
