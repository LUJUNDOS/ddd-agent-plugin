# CODEBUDDY.md（项目级，_template 默认，CodeBuddy 读此）

> 与 `CLAUDE.md`（Claude Code 读）内容一致，二选一维护须同步。**规则以本目录 CLAUDE.md 为准，二者不得分叉。**
> 详细规程在中枢 `methods/`（跨项目复用）。

## 1. DDD 四道闸门（MUST）
- 文档事实链：`docs/00-vision → 01-requirements → 02-architecture → 03-design → 04-tasks`。
- G0：00/01 `approved` 才写 02。G1：02/03 `approved` 才拆 04/写码。
- G2：每任务前用 `python scripts/ddd_gate.py check-module docs --module <path>` 确认 03-design `approved`，否则**拒写生产码**。
- G3：对照 01 验收标准全绿才 `done`。

## 2. 偏离铁律
实现发现设计问题 → **禁改码将就** → 回 `docs/` 改（重评审）→ 继续。「实现偏离」=代码错，非文档过时。

## 3. 角色人格（规划/设计戴帽串行；执行/测试/审查分发并行）
- 产品经理：澄清需求、消歧 → 00/01。架构师：四维并行调研 → 法庭式对抗选型（2+ 候选时红队+法官）→ ADR + 复用举证 → 02。规程见 `methods/adversarial-selection.md`。PM：拆 04-tasks。
- 开发：TDD 隔离 worktree。测试：出验证证据。审核：grill-with-docs 查偏离。

## 4. 并行安全规则
仅「任务无交叉」才并行，各自独立 worktree；必改同一文件 → 串行。

## 5. 验证者隔离 + 用户 Oracle
验证器独立上下文，只持验收标准+diff；G3 人工验收不可跳过。

## 6. 三道刹车
max_iter / Token 预算 / 停滞检测。

## 7. 工具纪律
密钥/产物绝不入库；写码前 check-module；commit 前 Hook 硬拦 ddd_gate（含 CHANGELOG mtime 拦截 + TASK 勾选 WARNING）。
- **TASK 勾选检查**：`ddd_gate.py check-tasks docs` 扫 04-tasks.md 未勾选 TASK，在 `validations/`、`contracts/C-*.md`（status=done）、`tasks/logs/` 中搜验证证据，有证据但未勾选 → WARNING。集成在 `gates --strict` 和 `pre-commit` 中。
- **路径约定**：`kb/raw/`、`kb/wiki/`、`methods/`、`logs/` 均指**工作区根目录**（含 `AGENTS.md` 的目录）下的路径，**不是项目级目录**。项目级不设 `kb/` 目录。`/ingest` 写入的 raw 文件必须落到工作区根 `kb/raw/<bucket>/`，不得写到 `projects/<proj>/kb/raw/`。
- **记忆日志（MUST）**：每次实质工作（写码/修 bug/重构/技术决策）后，向上找到工作区根目录（含 `AGENTS.md` 的目录）的 `.workbuddy/memory/`，追加一条简短记录到当天文件 `YYYY-MM-DD.md`（不存在则创建）。内容：改了什么 / 为什么 / 遇到什么坑。这是 `evolution_scan.py` 的数据源——不写 = 进化系统看不到。

## 8. 进化系统
规范见 `docs/EVOLUTION.md`；扫描器 `scripts/evolution_scan.py`。Phase 完成后或用户说"进化扫描"时手动运行。扫描日志 → 提取模式 → 生成提案到 `proposals/` → 用户审批后执行。双向进化（加规则 + 退休规则）。非自动，里程碑驱动。
