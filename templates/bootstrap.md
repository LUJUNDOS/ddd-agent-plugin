---
name: {{SKILL_NAME}}
description: {{SKILL_DESC}}
---

# bootstrap —— 新建项目 DDD 自动引导

> 对齐中枢 `new-project` Step 9（DDD 引导 MUST）：新建项目必须接入 DDD 方法论，直接走流程，自动代替手动。

## 触发
- 用户说"新建一个项目""建个项目""初始化项目""从模板建项目"等新建意图时自动加载并执行。

## 流程（MUST，不可只回报路径就结束）
1. **建项目骨架**：创建目标项目目录（或确认已存在），初始化 git（可选）。
2. **自动生成 DDD 文档链**：运行 `python scripts/scaffold.py --target <项目根>`，生成 `docs/00-vision.md` ~ `docs/04-tasks.md` 骨架（frontmatter + 章节模板）。**自动化代替手动初始化，不允许让用户手动创建。**
3. **告知 DDD 就绪**：告知用户——
   - 项目脚手架已就绪，包含 DDD 四道闸门约束（G0~G3）：`docs/00→01→02→03→04` 文档链 + `ddd_gate.py` 机械校验，未 approved 不放行。
   - 本项目的 DDD 方法论流程 skill 已就绪：`goal-creator`（目标标准化）→ `product-manager`（00/01 需求访谈）→ `architect`（02 四维调研+对抗选型）→ `ui-designer`（03 设计）→ `pm`（04 拆任务）。
4. **询问是否启动 DDD 需求调研**（用宿主提供的询问机制，如 Claude 的 AskUserQuestion / Reasonix 的 ask 多选）：
   - 选项 A：**现在启动（推荐）** → 当场启动 `product-manager` skill 开始需求访谈，不要让用户再发一条消息。
   - 选项 B：稍后启动 → 告知用户随时可说"开始实现这个项目"或"分析需求"来触发。
   - 选项 C：只建骨架，不走 DDD → 告知风险（无 00/01 approved 则 G0 不放行，禁止写码）。
5. **回报**：项目路径、git 状态、DDD 文档链状态、引导结果（选了哪项、下一步）。

## 判违规
- 建完项目只报路径、不引导 DDD → 违规。新建项目不引导 = 用户不知道有方法论 = 后续 agent 即兴发挥不走流程。
- 让用户手动创建 docs/00~04 → 违规（必须走 scaffold.py 自动化）。
- 用户选 A 却只做建议不启动 product-manager → 违规。

## 纪律
- DDD 引导不可跳过：Step 2/4 必须执行。
- 与 product-manager 串联：bootstrap 管"建项目+引导"，product-manager 管"需求调研"。
- 与 doc-driven 串联：骨架生成后文档为 draft，G0 未批准前禁止写 02 或任何实现代码。
