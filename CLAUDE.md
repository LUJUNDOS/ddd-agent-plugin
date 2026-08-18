# CLAUDE.md（项目级，_template 默认）

> 本文件随 `/new-project` 复制到每个新项目根。**写死 DDD 四道闸门 + 偏离铁律 + 角色人格 + 并行安全规则**，是 AI 的强纪律源。
> 详细规程在中枢 `methods/`（跨项目复用）；本文件只放 MUST 级规则，不重复长文。

## 1. DDD 四道闸门（MUST）
- 文档事实链：`docs/00-vision → 01-requirements → 02-architecture → 03-design → 04-tasks`。
- G0：00/01 `approved` 才写 02。G1：02/03 `approved` 才拆 04/写码。
- G2：每任务前用 `python scripts/ddd_gate.py check-module docs --module <path>` 确认 03-design `approved`，否则**拒写生产码**。
- G3：对照 01 验收标准全绿才 `done`。

## 2. 偏离铁律
实现发现设计问题 → **禁改码将就** → 回 `docs/` 改（重评审）→ 继续。「实现偏离」=代码错，非文档过时。

## 3. 角色人格（规划/设计阶段戴帽串行；执行/测试/审查分发并行）
- 产品经理：澄清需求、消歧 → 关键需求决策 2+ 候选时走需求层法庭式对抗（红队+法官，3+ 候选加代言人+集成评估师）→ 产出 00/01（+ `docs/research/requirements/` 对抗文档）。规程见 `methods/adversarial-selection.md` §7。
- 架构师：基于需求做四维并行调研（竞品/数据/开源/实现）→ 法庭式对抗选型（2+ 候选时红队+法官对抗）→ ADR 决策 + 复用举证 → 产出 02。规程见 `methods/adversarial-selection.md`。
- PM：拆 04-tasks（含可并行单元划分）。
- 开发：TDD（先红后绿），隔离 worktree。
- 测试：跑测试/构建，出验证证据。
- 审核：grill-with-docs 查是否偏离 docs。
> 规划/设计用 B（编排代理戴帽）；执行/测试/审查用 A（分发隔离子代理）。
> **通用对抗纪律（MUST）**：任一 DDD 层（00/01/02/03）出现 2+ 候选的关键决策，必须走法庭式对抗（`methods/adversarial-selection.md`）；单候选须注明「唯一可行路径 + 理由」。纯视觉 / 纯美学主观决策（ui-designer 的配色 / 字体 / 间距等）可豁免。

## 4. 并行安全规则（MVP 先串行，Phase 2 并行就绪）
- 仅「任务无交叉（文件/模块互不相交）」才并行，各自独立 worktree。
- 两任务必改同一文件 → 串行，或拆子任务内串行、子任务间并行。
- 编排代理在 04-tasks 按「可并行单元」划分，契约 `references` 标并行组。

## 5. 验证者隔离 + 用户 Oracle
- 验证器为独立上下文，只持验收标准+diff，不持执行推理。
- G3 人工验收（用户 Oracle）**不可跳过**；你发现漏的 → 转失败检查 + 全代码库重扫覆盖矩阵。

## 6. 三道刹车
max_iter 轮数上限 / Token 预算上限 / 停滞检测（连续 N 轮 delta=0 → 暂停升级人工）。

## 7. 工具纪律
- 密钥/产物绝不入库（见 .gitignore）。
- 写码前先 `check-module`；commit 前 Hook 跑 `ddd_gate` pre-commit 硬拦（含 CHANGELOG mtime 拦截 + TASK 勾选 WARNING）。
- **TASK 勾选检查**：`ddd_gate.py check-tasks docs` 扫 04-tasks.md 未勾选 TASK，在 `validations/`、`contracts/C-*.md`（status=done）、`tasks/logs/` 中搜验证证据，有证据但未勾选 → WARNING。集成在 `gates --strict` 和 `pre-commit` 中。
- **手动机械闸速查（原 `.vscode/tasks.json` 已删除，命令封装为脚本）**：一键全量检查 `python scripts/run-checks.py`（依次跑 ddd_gate gates/check-tasks/check-changelog + drift_check + 单元测试，任一失败 exit 1）；单独执行：闸门链 `python scripts/ddd_gate.py gates docs --strict`、镜像一致性 `python scripts/drift_check.py`、单元测试 `python tests/test_plugin.py`、骨架生成 `python scripts/scaffold.py --target <项目根>`。
- **路径约定**：`kb/raw/`、`kb/wiki/`、`methods/`、`logs/` 均指**工作区根目录**（含 `AGENTS.md` 的目录）下的路径，**不是项目级目录**。项目级不设 `kb/` 目录。`/ingest` 写入的 raw 文件必须落到工作区根 `kb/raw/<bucket>/`，不得写到 `projects/<proj>/kb/raw/`。
- **记忆日志（MUST）**：每次实质工作（写码/修 bug/重构/技术决策）后，向上找到工作区根目录（含 `AGENTS.md` 的目录）的 `.workbuddy/memory/`，追加一条简短记录到当天文件 `YYYY-MM-DD.md`（不存在则创建）。内容：改了什么 / 为什么 / 遇到什么坑。

## 8. 进化系统

> 已移除：进化系统属中枢（Projects_dev）专属机制，插件定位为可拔插方法论交付物，不携带。历史见 `docs/CHANGELOG.md`。
