---
status: approved
title: 03-design
layer: 03
related: [02-architecture]
---

# 03-design —— ddd-agent-plugin 详细设计

> 依据 02-architecture（AD-0001~0004）。每模块实现前须本层 approved（G2 闸门）。

## 1. 插件包目录结构（单一源）

```
ddd-agent-plugin/
├── plugin.manifest.yaml        # 单一源：元数据 + skill 清单 + 宿主声明
├── templates/                  # 宿主无关 skill 正文（6 份）
│   ├── doc-driven.md
│   ├── gate.md
│   ├── verify.md
│   ├── review.md
│   ├── no-fake-test.md
│   └── memory-protocol.md
├── hosts/                      # per-host 适配片段
│   ├── reasonix/layout.json
│   └── claude/layout.json
├── scripts/                    # 插件自带工具（含复用蓝本的 ddd_gate.py）
│   ├── generate.py
│   ├── drift_check.py
│   ├── install.py
│   ├── uninstall.py
│   └── ddd_gate.py             # 复用蓝本，随插件分发
├── docs/                       # 本项目 DDD 文档链（00~04 + research/）
├── CLAUDE.md / CODEBUDDY.md    # 项目自身规则
└── .gitignore
```

## 2. `plugin.manifest.yaml` Schema

```yaml
id: ddd-agent-plugin
version: 0.1.0
license: MIT
description: "DDD 方法论可拔插 agent 插件：5 纪律 skill + 记忆规程 + 机械闸"
skills:
  - id: doc-driven        # → templates/doc-driven.md
    title: 文档驱动闸门
    trigger: 写码前自动加载
  - id: gate
    title: 结构闸
  - id: verify
    title: 行为真证
  - id: review
    title: 收口审查
  - id: no-fake-test
    title: 测试真实性闸
  - id: memory-protocol
    title: 记忆规程
hosts:                        # 支持声明（FR-009）
  reasonix: { status: verified, layout: hosts/reasonix/layout.json }
  claude:   { status: verified, layout: hosts/claude/layout.json }
  codebuddy:{ status: planned }   # P1
  codex:    { status: planned }   # P1
```

## 3. `hosts/<host>/layout.json` Schema（宿主差异收敛点）

```json
{
  "base_dir": ".reasonix/skills",        // 相对宿主项目根；claude 用 ".claude/skills"
  "skill_dir": "<skill-id>",
  "skill_file": "SKILL.md",
  "frontmatter": {                       // 各宿主 frontmatter 规则
    "name_field": "name",
    "description_field": "description",
    "extra_fields": ["triggers"]
  }
}
```

## 4. `scripts/generate.py` 接口

```
python generate.py [--host <name|all>] [--out dist]
```
- 读 `plugin.manifest.yaml` → 对每个 skill：读 `templates/<id>.md`，按 `hosts/<host>/layout.json` 生成 `<out>/<host>/skills/<id>/SKILL.md`
- frontmatter 转换：正文内 `{{SKILL_NAME}}`、`{{SKILL_DESC}}` 占位符由 manifest 填充
- 产物：`dist/<host>/` 完整镜像（skill 目录树 + 拷贝的 ddd_gate.py）
- 纯标准库（`string.Template`），无第三方依赖（NFR-01）

## 5. 6 份 skill 内容规格（正文=约束型：只写验收标准，不写人格）

统一 frontmatter 结构（reasonix 示例）：
```yaml
---
name: doc-driven
description: 文档驱动闸门：写码前校验 G0~G3 文档链闭合
---
```

| skill | 验收标准要点（对齐蓝本） |
|-------|------------------------|
| doc-driven | G0：00/01 approved 才写 02；G1：02/03 approved 才拆 04/写码；G2：每任务前 check-module；G3：对照 01 验收全绿才 done |
| gate | 写码后提交前跑 ddd_gate.py gates + drift_check，非零即拦 |
| verify | 对照 DoD/验收标准隔离验证；独立上下文，只持验收标准+diff |
| review | Done 前独立 reviewer PASS；自述完成无效 |
| no-fake-test | 同义反复/反向断言/只测顺路径/mock 被测物/静默跳过 → FAIL |
| memory-protocol | 何时记（错误复盘/决策/经验）/ 记什么（[schema §6]）/ 如何回溯（会话开头读宿主记忆）；落点=宿主原生记忆，**插件不建 kb** |

## 6. 记忆规程 Schema（memory-protocol 核心）

```yaml
事件类型: [error|decision|insight]
schema:
  error:    { symptom, root_cause, fix, verified_by, date }
  decision: { context, options, chosen, rationale, date }
  insight:  { topic, takeaway, applies_to }
落点映射（宿主原生，AD-0002）:
  reasonix: memory 工具 / .reasonix/skills 伴生 memory.md
  claude:   CLAUDE.md 追加 + memory/ 目录
回溯: 新会话开头检索宿主记忆中的 error/decision 类型
```

## 7. `install.py` / `uninstall.py` 规格

```
python install.py --host <name>            # 生成+复制+登记
python uninstall.py --host <name>          # 按登记清单删除
```
- install：调用 generate → 复制到宿主 skill 目录 → 写 `<out>/<host>/manifest-installed.json`（文件清单+hash）
- uninstall：读清单 → 逐文件删除 → 校验宿主目录与安装前快照一致（AC-5）
- 幂等：重复 install 覆盖更新；uninstall 不存在清单时拒绝执行

## 8. `drift_check.py` 规格

```
python drift_check.py [--host <name|all>] [--out dist]
```
- 重新生成 dist 并与现有镜像 diff → 输出漂移报告（文件级 + frontmatter 级）
- 退出码：0=一致；1=漂移（供 hook/CI 拦截，FR-003）

## 9. 宿主侧目标布局（生成结果）

```
reasonix 宿主：  <proj>/.reasonix/skills/{doc-driven,gate,verify,review,no-fake-test,memory-protocol}/SKILL.md
claude 宿主：    <proj>/.claude/skills/{doc-driven,gate,verify,review,no-fake-test,memory-protocol}/SKILL.md
机械闸：         随镜像分发 scripts/ddd_gate.py（可选，宿主无 python 时降级为纯文档约束）
```

## 10. 测试设计（G3 证据来源）

| 用例 | 验证点 | 对应 AC |
|------|--------|---------|
| UT-1 generate 幂等 | 两次生成产物一致 | AC-1 |
| UT-2 drift 检出 | 篡改镜像后 drift_check 非零 | AC-1 |
| UT-3 install/uninstall 可逆 | 卸载后宿主目录与安装前快照 diff 为空 | AC-5 |
| UT-4 包内容无 kb | 产物清单断言无 kb/ 文件 | AC-4 |
| E2E-1 reasonix 真机 | 安装后 5 skill 可触发 + ddd_gate 拦截生效 | AC-2/7 |
| E2E-2 claude 真机 | 同上 | AC-3/7 |
