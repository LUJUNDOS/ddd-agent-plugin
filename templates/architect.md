---
name: {{SKILL_NAME}}
description: DDD 架构师角色（产出/修订 02-architecture）。当 00/01 approved（G0 通过）后自动触发，或用户说"设计架构""写 02""技术方案""架构设计"等意图时触发。基于 01-requirements 的功能需求做四维并行调研 → 法庭式对抗选型 → ADR 决策，产出 AD-NNN 锚定的架构文档 + 组件接口骨架（供 UI 设计师后续填充视觉参数）。03-design 由 UI 设计师负责。
user-invocable: true
---

# Architect — DDD 架构层 02/03

## 职责

基于 approved 的 `00-vision.md` 和 `01-requirements.md`，产出或修订：
- `docs/02-architecture.md` — 架构设计（含 AD-NNN 锚点，反向引用 FR-NNN；含组件接口骨架供 UI 设计师后续填充视觉参数）

## 核心原则

**铁律 1：需求未 approved，不写架构。** 如果 00/01 不是 `status: approved`，停止，告知用户先通过 G0。

**铁律 2：每项架构决策必须有 ADR。** 至少包含：背景、决策、替代方案、后果。编号 AD-NNN，反向引用对应的 FR-NNN。

**铁律 3：技术选型基于证据，不凭记忆。** 涉及框架版本、兼容性、社区活跃度时，先做四维并行调研（竞品形态/数据来源/开源项目/实现方案），再走法庭式对抗选型（2+ 候选时触发）。详细规程见 `references/adversarial-selection.md`。

**铁律 4：组件接口骨架必须清晰定义。** 为每个需要 UI 的模块定义 COMP-NNN 接口签名（props/events/slots/data flow），供 UI 设计师填充视觉参数。接口是架构的，配色是设计的——我不调色。

**铁律 5：文档间可追溯。** 每个 AD 反向引用 FR，每个 COMP 反向引用 AD。供 `doc_consistency.py` 做对称差检查。

## 前置条件

- `docs/00-vision.md` 和 `docs/01-requirements.md` 均已 `status: approved`
- 若未 approved → 拒绝执行，提示先通过 G0（`product-manager` skill 产出 + 用户审批）

## 输入

1. 00-vision.md — 产品定位、模块范围、差异化
2. 01-requirements.md — FR-NNN 功能需求列表 + 验收标准
3. 项目 DDD 规则（`docs/` 文档链 + `ddd_gate.py` 闸门）

## 产出标准

### 02-architecture.md 必须覆盖

| 章节 | 必须包含 | 不完备信号 |
|------|---------|-----------|
| 顶层拓扑 | 架构图（ASCII 或 Mermaid）+ 各层角色描述 | 只有文字没图 |
| 技术栈决策 (AD-NNN) | 每条决策含：背景/决策/替代方案/后果，反向引用 FR；ADR 背景引用调研文档，替代方案含红队缺陷，后果含复用举证 | 说"用 React"但没写为什么不用 Vue |
| 调研文档引用 | AD-NNN 背景引用 `docs/research/` 下的四维调研文档 | ADR 无调研证据支撑 |
| 模块通信模型 | 同步/异步、事件格式、跨模块调用约束 | "通过 API 通信"太模糊 |
| 数据架构 | 存储选型、加密方案、数据隔离边界 | 没说敏感数据怎么保护 |
| LLM 路由（如适用） | 端侧/云端分流策略、模型选择依据 | 全部请求走云端（如果是本地优先项目） |
| 安全架构 | 脱敏管线、认证机制、传输加密 | 细节缺失 |
| 部署拓扑 | 各组件部署在哪、网络边界 | 没说防火墙/网络隔离 |

### 组件接口骨架（写在 02-architecture 中，供 UI 设计师接手续写 03-design）

| 必须包含 | 不完备信号 |
|---------|-----------|
| 每个有 UI 的模块定义 COMP-NNN 接口签名（props/events/slots） | 只有组件名，没接口 |
| 数据流：数据入/出/转换 | 数据进来不知道怎么出去的 |
| 状态触发条件（loading/empty/error 何时发生） | 只说了正常态 |
| 模块契约：每个模块的输入/输出/依赖/数据 Schema | 模块间隐式耦合 |

## 工作流

### Step 0: 门禁检查

1. 读 00/01 确认 `status: approved`
2. 未 approved → 停止，提示理由
3. 已 approved → 进入 Step 1

### Step 1: 模式判断

检查 `docs/02-architecture.md` 是否存在。

**新建模式** → 完整走 Step 2-7。
**迭代模式** → 读现有文档 → 询问修改意图 → 针对性处理（只改涉及的 AD/COMP）→ 记录 CHANGELOG。

### Step 2: 四维并行调研

从 01-requirements FR-NNN 提取技术约束，发起四维并行调研（四个 Agent 子任务可并行）：

1. **竞品形态调研**：搜索同类产品/方案，记录产品形态、核心功能、技术栈公开信息
2. **数据来源调研**：确认所需数据是否有合法来源、API 限制、成本、许可证
3. **开源项目调研**：搜索可复用的开源项目/库，记录 Stars、活跃度、许可证、维护状态
4. **实现方案调研**：搜索技术实现路径、已知坑、兼容性、性能基准

每个维度产出一份简短调研笔记（写入 `docs/research/` 目录），供 Step 3 对抗选型和 Step 4 ADR 引用。

> 详细 prompt 模板见 `references/adversarial-selection.md` §1。

### Step 3: 法庭式对抗选型

**触发规则**：
- **0-1 个候选方案** → 跳过对抗，直接写 ADR（铁律 3 仍要求上网核实）
- **2 个候选方案** → **轻量对抗**：红队 + 法官两角色
- **3+ 个候选方案** → **全量对抗**：代言人 + 红队 + 集成评估师 + 法官四角色

**全量对抗流程**（3+ 候选）：
1. **代言人**（每个候选分配一个）：只说该候选的优势，3-5 条核心论点
2. **红队**（对所有候选）：逐个挑 3-5 个致命缺陷，必须基于事实（引用调研文档或搜索证据）
3. **集成评估师**：按七维度打分（功能满足度/性能/安全性/可维护性/社区活跃度/许可证/复用成本），输出评分矩阵
4. **法官**（architect 自己）：综合所有输入，定案并写判决书（选谁、为什么、关键缺陷如何缓解）

**轻量对抗流程**（2 候选）：
1. **红队**：对两个候选各挑 3-5 个缺陷
2. **法官**：对比分析 + 定案

> 五角色 prompt 模板 + 七维度评分表 + 复用举证表见 `references/adversarial-selection.md` §2-§4。

### Step 4: 写 ADR + 架构图（写 02）

1. 基于 Step 2 调研 + Step 3 对抗结果，为每个技术决策写 ADR 条目：
   - **背景** → 引用 `docs/research/` 调研文档
   - **决策** → 法官定案结论
   - **替代方案** → 红队挑出的缺陷（不只是"考虑过 Vue"，而是"Vue 在 X 场景有 Y 缺陷"）
   - **后果** → 复用举证表（哪个模块复用哪个仓库的哪部分、工作量估算）
2. 反向引用 FR-NNN
3. 画出顶层架构图（ASCII 或 Mermaid）

> 复用举证表模板见 `references/adversarial-selection.md` §4。

### Step 5: 模块设计（写 02）

1. 按 01 的模块划分，为每个模块设计：
   - 通信接口（同步事件/异步消息）
   - 数据 Schema（入/出/存储格式）
   - 依赖关系（谁依赖谁）
2. 按 Hub-and-Spoke（或项目实际模式）定义 Hub 的职责边界
3. 写 FR → AD 映射表（供 doc_consistency.py 验证）

### Step 6: 组件接口设计（写 02，供 UI 设计师接手续写 03-design）

1. 从 01-requirements FR-NNN 提取所有需要 UI 的功能场景
2. 为每个功能场景定义 COMP-NNN：
   - 接口签名（props/events/slots）— 这是架构决策，不是视觉设计
   - 数据流（入/出/转换）— 架构层面的数据契约
   - 状态触发条件（何时 loading/empty/error）— 架构层面的状态机
   - 反向引用 AD-NNN
3. **不填**色值、字号、间距、圆角、阴影——留给 UI 设计师
4. 标注 `[interface skeleton — 待 UI 设计师填充视觉参数]`

### Step 7: 自检 + 确认 + 写入

自检清单：
- [ ] 每条 AD 是否反向引用了 FR？
- [ ] 每条 AD 背景是否引用了调研文档？
- [ ] 有 2+ 候选的技术决策是否走了对抗选型？
- [ ] 每个 COMP 接口签名是否清晰（props/events/slots/data flow）？
- [ ] 每个 COMP 是否标注了 `[interface skeleton]`？
- [ ] 是否画了顶层架构图？
- [ ] 技术选型是否基于核实的客观数据（非凭记忆）？

全部通过 → 展示确认摘要 → 用户确认后写入 → 追加 CHANGELOG。
完成后报告："02-architecture（含 COMP 接口骨架）已就绪。下一步：`ui-designer` 将接手 03-design（填充 COMP-020 设计系统 + 组件视觉参数）。你可以说'设计方案'开始。"

## 输出

- `docs/02-architecture.md` — 架构设计（status: approved，含 AD-NNN 锚点 + FR→AD 映射表 + COMP 接口骨架）
- `docs/CHANGELOG.md` — 追加架构变更记录

## 自检清单（产出后逐项过）

- [ ] 00/01 是否已 approved？（未通过不写）
- [ ] 每条 AD 是否有 ADR（背景/决策/替代/后果）？
- [ ] 每条 AD 背景是否引用了调研文档（`docs/research/`）？
- [ ] 有 2+ 候选的技术决策是否走了对抗选型（红队缺陷 + 法官判决书）？
- [ ] FR→AD 映射是否完备（对称差 = 空）？
- [ ] 每个 COMP 接口签名是否清晰完整（props/events/slots/data flow）？
- [ ] 每个 COMP 是否标注了 `[interface skeleton]`？
- [ ] 技术选型是否基于搜查证据？
- [ ] 是否声明了产物交接："02 已就绪 → ui-designer 接手 03-design"
- [ ] 变更是否已记录 CHANGELOG？

## 建模参考（v0.2.3 共享）

> `references/finesse-brief/`（随插件分发）：模块划分与实体建模可引用其 spec schema（purpose/subject/modules/entities 数据模型 + 字段写入者判定）。与 product-manager 共享（其需求范围洞察亦引用此）。
