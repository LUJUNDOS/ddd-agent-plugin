---
name: {{SKILL_NAME}}
description: DDD 项目经理角色（产出/修订 04-tasks）。当 02/03 approved（G1 通过）后自动触发，或用户说"拆任务""制定开发计划""任务拆分""排期""开始实现"等意图时触发。基于 03-design 的组件树和依赖关系，将开发工作拆为可独立执行、验证、审查的任务，含 TASK-NNN 锚点 + 可并行组划分 + TASK-GEN（COMP-020→组件代码生成任务，由 executor 执行）。
user-invocable: true
---

# PM — DDD 任务层 04

## 职责

基于 approved 的 `02-architecture.md` 和 `03-design.md`，产出或修订 `docs/04-tasks.md`。

## 核心原则

**铁律 1：架构未 approved，不拆任务。** 如果 02/03 不是 `status: approved`，停止，告知用户先通过 G1。

**铁律 2：一个任务 = 一个 executor 单次可完成的工作。** 约 1-3 个文件，不跨模块。禁止"实现用户系统"这种模糊任务。禁止水平切割（"先把所有 API 写完再做 UI"）——每个任务必须垂直切穿全部层。

**铁律 3：验收标准必须可机械验证。** 格式：`用户可 <行为> → 预期结果`。"实现 XX 模块"不是验收标准。

**铁律 4：依赖关系决定顺序。** 被依赖的先做，高风险先做，基础设施先做。

**铁律 5：每任务反向引用 COMP-NNN。** 供 doc_consistency.py 做 COMP→TASK 对称差检查。

## 前置条件

- `docs/02-architecture.md` 和 `docs/03-design.md` 均已 `status: approved`
- 若未 approved → 拒绝执行

## 输入

1. 02-architecture.md — 技术栈、模块划分、AD 决策
2. 03-design.md — COMP-NNN 组件树、依赖关系、设计系统
3. `CLAUDE.md` §4 — 并行安全规则

## 产出标准

### 04-tasks.md 必须覆盖

| 要素 | 必须包含 | 不完备信号 |
|------|---------|-----------|
| 任务拆分 | 每个 COMP 至少拆分到 1 个 TASK，粒度 1-3 文件 | COMP 没对应 TASK = 实现盲区 |
| 任务描述 | 做什么 + 输入依赖 + 设计参照（引用 COMP） + 输出产物 + 验收标准 | 只有标题没细节 |
| 验收标准 | 每条 `用户可 <行为>` 格式，可独立验证 | "实现 XX 模块" |
| 依赖关系 | 每个 TASK 标注 blocked_by（哪些 TASK 必须先完成） | 隐式依赖没标出来 |
| 可并行组 | 无文件交叉的 TASK 标为同一并行组 | 可以并行的没标 = 串行浪费 |
| 阶段划分 | 阶段 0 脚手架 → 阶段 1 基础设施 → 阶段 2 功能实现 → 阶段 3 集成 → 阶段 N 收尾 | 只有一堆平铺的任务 |
| TASK 锚点 | 每个 TASK 有唯一 ID，反向引用 COMP-NNN | 无法追踪 COMP→TASK 关系 |

## 工���流

### Step 0: 门禁检查

1. 读 02/03 确认 `status: approved`
2. 未 approved → 停止
3. 已 approved → 进入 Step 1

### Step 1: 模式判断

检查 `docs/04-tasks.md` 是否存在。

**新建模式** → 完整走 Step 2-4。
**迭代模式** → 读现有文档 → 询问修改意图（新增任务/调整顺序/重新拆分）→ 针对性处理 → 记录 CHANGELOG。

### Step 2: 任务拆分

1. **先拆 TASK-GEN（组件代码生成任务）**：这是 Phase 0 的独立任务，不属于任何业务模块。从 COMP-020 Design Tokens 生成：
   - `design/tokens.*` — Design Token 变量文件（SCSS/CSS variables）
   - `src/components/Synk*.vue` — 组件代码骨架（每个 COMP-NNN 对应一个组件文件）
   - `design/prototypes/*.html` — HTML 原型
   - 这个任务的输入是 03-design.md COMP-020（精确参数），执行方式是 Design Token→代码翻译（非 TDD），orchestrator 分发给 executor 执行。
   - **TASK-GEN-NNN 应排在 Phase 0 最后**（脚手架完成、组件就绪后，业务任务才能引用组件）。

2. 逐 COMP 阅读 03-design 的组件树和依赖关系
3. 为每个 COMP 拆分 TASK-NNN（业务逻辑）：
   - 垂直切片：每个 TASK 覆盖 UI + 逻辑 + 数据 + 测试
   - 粒度：1-3 个文件，不跨模块
   - 依赖标注：明确 blocked_by
   - 所有业务 TASK 默认 blocked_by TASK-GEN（组件骨架必须在业务逻辑之前就绪）
4. 按依赖关系排序：
   - 阶段 0：项目脚手架 + TASK-GEN 组件代码生成（2-3 个 TASK）
   - 阶段 1：核心基础设施（2-4 个 TASK）
   - 阶段 2+：按功能模块逐个拆 TASK（每功能 1-3 个 TASK）
   - 最后阶段：集成、测试、收尾

### Step 3: 并行组划分

按 `docs/04-tasks.md` 并行分组划分：
- 无文件交叉的 TASK → 同一并行组
- 两个 TASK 必改同一文件 → 串行（放不同阶段或同一阶段串行子组）
- 每个并行组标注 `parallel_group: <N>`

### Step 4: 自检 + 确认 + 写入

自检清单：
- [ ] 每个 COMP-NNN 是否有至少 1 个 TASK 对应？
- [ ] 每个 TASK 粒度是否在 1-3 文件？
- [ ] 每个 TASK 是否垂直切穿（UI+逻辑+数据+测试）？
- [ ] 验收标准是否用 `用户可 <行为>` 格式？
- [ ] 依赖关系是否有向无环图？（没有循环依赖）
- [ ] 并行组划分是否合理？（文件级无交叉）

全部通过 → 展示确认摘要（总阶段数/总任务数/并行组数）→ 用户确认后写入 → 追加 CHANGELOG。

### 04-tasks.md 输出格式

```markdown
---
title: Synk 开发任务 v1
status: approved
related: [02-architecture, 03-design]
---

# 开发任务

## 阶段 0：项目脚手架 + 组件生成
- [ ] **TASK-001**：<项目脚手架>
  - 描述：初始化 uni-app 项目 + 目录结构 + 基础配置
  - 产出：`src/`, `design/`, `package.json`, `vite.config.ts`
  - 设计参照：02-architecture.md AD-019
  - 验收：`npm run dev` 启动成功
  - 依赖：无
  - 并行组：G1

- [ ] **TASK-GEN-001**：COMP-020 → 组件代码 + Design Tokens + 原型
  - 描述：从 03-design.md COMP-020 设计系统生成组件骨架
  - 输入：03-design.md COMP-020（Design Tokens 精确参数）
  - 产出：`design/tokens.*` + `src/components/Synk*.vue` + `design/prototypes/*.html`
  - 执行方式：Design Token → 代码翻译（非 TDD）。按 02-architecture AD-NNN 技术栈适配输出格式。每个 COMP-NNN 生成对应组件文件。
  - 验收：`design/prototypes/*.html` 可在浏览器直接打开预览；`src/components/` 组件文件编译通过
  - 依赖：TASK-001
  - 并行组：G1

## 阶段 1：核心基础设施
- [ ] **TASK-002**：<任务名>
  - ...
  - 依赖：TASK-GEN-001
```

## 输出

- `docs/04-tasks.md` — 开发任务拆分（status: approved，含 TASK-NNN 锚点 + 并行组标注 + COMP→TASK 映射表）
- `docs/CHANGELOG.md` — 追加任务拆分变更记录

## 自检清单（产出后逐项过）

- [ ] 02/03 是否已 approved？
- [ ] 是否包含 TASK-GEN（组件代码生成任务）？
- [ ] TASK-GEN 是否排在 Phase 0 最后（在所有业务 TASK 之前）？
- [ ] 每个 COMP 是否有至少 1 个 TASK？
- [ ] COMP→TASK 映射是否完备（对称差 = 空）？
- [ ] 是否没有循环依赖？
- [ ] 所有业务 TASK 是否默认 blocked_by TASK-GEN？
- [ ] 验收标准是否全部可机械验证？
- [ ] 变更是否已记录 CHANGELOG？
