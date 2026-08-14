# CHANGELOG

## [0.2.3] - 2026-08-13

### 新增（设计能力融合，FR-017/018/AC-11）
- `references/design-dna/`（全量 4 份：SKILL + generation-guide + schema + LICENSE，MIT）。
- `references/finesse-ui/`（精选 13 份：SKILL + 12 方法论精华；**不含 HTML 示例/JS 库**）。
- `references/finesse-brief/`（核心 5 份：SKILL + grammar/system-domain/discovery/starters，共享）。
- `ui-designer` 增强：DNA 提取 / 高工艺构建 / 反廉价审计三维能力 + references 引用。
- `product-manager` / `architect`：补 finesse-brief 共享引用（结构分类 / 模块实体建模）。
- `generate.py` references 拷贝改递归（子目录）；manifest references 加 3 目录；测试扩展（AC-11 资产断言）。
- 交付收尾：manifest version 0.2.2→0.2.3；README 特性表补"设计能力"行 + 版本标注 v0.2.3；04-tasks 补 TASK-0017；validations/run-7.md；中枢日志 R-0016。
- 合规补充：finesse-ui/finesse-brief 补 LICENSE（MIT 模板）；`references/NOTICE.md` 集中声明 3 个第三方 MIT 子目录（版权人/许可/来源/再分发条件）；各 README 与根 README 补来源说明与第三方声明章节。
- 第三方出处查实：design-dna ← zanwei/design-dna（1405⭐）；finesse-ui ← mouse-lin/finesse-skill（435⭐）；finesse-brief ← mouse-lin/finesse-brief——NOTICE/README 来源链接更新。
- 版权声明：新增根 `LICENSE`（MIT，Copyright (c) 2026 LUJUNDOS）；README 许可章节补版权人。
- 终审验证：覆盖率实测 100%（标准库 trace，5 脚本）；重复 install 幂等（hooks 不重复挂载）；端到端全流程（install→scaffold→G0 拦截→卸载零残留）通过。
- 需求追溯矩阵：FR-001~018 全部有实现证据（18/18）+ NFR-01~05 全部满足（validations/run-7.md 记录）。

## [0.2.2] - 2026-08-13

### 新增
- `templates/evolution-scan.md`（长期区维护：退休 30 天规则 / 合并去重 / 冲突检测 / 跨项目提炼；晋升 ≥3 次归 memory-protocol，两 skill 分工无重复——修复初版"≥3 次重复"设计缺陷）；manifest skills 13→14；需求 FR-016/AC-10；03-design §16。

### 变更
- manifest version 0.2.0→0.2.2；04-tasks 补 TASK-0014~0016（v0.2.1/v0.2.2）；03-design §12 表补 evolution-scan 行。
- memory-protocol 补 evolution-scan 串联引用（记→维护双向闭环）；README/03-design 数字对齐 14 skill。
- AC-10 真机模拟通过（四类清单 / 用户确认闸 / 禁止重复 / 双向闭环）；validations/run-6.md 验收记录。
- 交付检查补验：claude_gate_hook.py 行为验证（拦截 draft→exit 2 / 放行 approved→exit 0 / 边界放行）；references 6 份 hash 核对（4 IDENTICAL + 2 含头部说明，符合预期）。

## [0.2.1] - 2026-08-13

### 新增（中枢同步审计修复）
- 补 `debug` skill（纪律层 6/6：doc-driven/gate/verify/review/no-fake-test/debug，宿主无关化）。
- 补 `references/doc-driven-dev.md`（DDD 详细规程打包，doc-driven skill 补引用）。
- 补 `scripts/claude_gate_hook.py`（PreToolUse 硬拦截脚本）。
- **hooks 自动挂载**：hosts layout 增 `hooks` 字段；install 合并写宿主 `settings.json`（保留原 hooks、先备份）；uninstall 恢复/删除；测试 TestHooks。
- `references/capability-registry.md` 打包（manifest 补充说明，4→5）。
- `references/performance-optimization.md` 打包（技术参考层，5→6）。

### 变更
- 移除 `.vscode/`（闸门任务封装为 `scripts/run-checks.py`）；`_template` 同步移除（源头治理）。
- 分享前清理：移除模板无关脚本（douyin_resolver / extract_browser_cookies / transcribe / kb_lint / evolution_scan / claude_gate_hook）与中枢专属进化系统（docs/EVOLUTION.md + CLAUDE/CODEBUDDY §8 改"已移除"）。
- 引用闭环修复：review/verify 补 `references/code-review-standard.md` 引用 + §7 适用边界。
- goal-creator 去 Loop 契约残留（contract_id/loop_type/owner_role/contracts/），产物改为目标清单。
- 交付文档对齐 v0.2.1：README 写码硬拦截行、13 skill/7 纪律/6 references；validations/run-4.md。

## [0.2.0] - 2026-08-13

### 新增（中枢同步）
- 需求 FR-012~015 + 验收 AC-8/9（`docs/01-requirements.md`）：新建项目 DDD 自动引导 / 角色 skill 链 / scaffold 骨架生成 / references 打包。
- 设计（`docs/03-design.md` §11~14）：bootstrap skill 流程、5 角色 skill 规格、references 打包、scaffold.py 接口。
- 任务 TASK-0009~0013（`docs/04-tasks.md`）。
- 实现：
  - `templates/bootstrap.md`：新建项目 DDD 自动引导（对齐中枢 new-project Step 9，宿主无关询问机制）。
  - `templates/{goal-creator,product-manager,architect,ui-designer,pm}.md`：5 角色流程 skill（从中枢 `.workbuddy/skills/` 提取，宿主无关化）。
  - `scripts/scaffold.py`：一键生成 docs/00~04 骨架（幂等，纯标准库）。
  - `references/`：打包 adversarial-selection / pm-thinking-guide / code-review-standard 3 份方法论。
  - `plugin.manifest.yaml`：skills 6→12、scripts +scaffold.py、references 声明；`generate.py` 纳入 references 拷贝。
  - `tests/test_plugin.py`：UT-5（scaffold 幂等）、UT-6（references 闭环），13 用例全绿。

### 修复（v0.2.0 真机验证发现）
- `install.py`/`uninstall.py`：备份目录按宿主分文件（`.ddd-agent-plugin-backup-<host>`），修复多宿主 install 的 backup 互相覆盖（真机验证抓出）。
- 回归测试：`TestMultiHostRoundtrip`（双宿主装→卸→全部恢复），14 用例全绿。
- 任务 TASK-0009~0013 全部勾选（validations/run-3.md）；README 快速开始补 bootstrap/scaffold 用法。

## [0.1.0] - 2026-08-13

### 新增
- G0 立项：`docs/00-vision.md`（可拔插 DDD 插件愿景 + 四大决策）、`docs/01-requirements.md`（11 FR + 5 NFR + 7 AC），经用户 Oracle 批准 approved。
- 调研：`docs/research/competitors.md`（GitHub API 实证：SDD 插件赛道头部真空、单宿主、组合空白）；`docs/research/selection-ddd-agent-plugin.md`（法庭式对抗选型：B 自建 30/35 胜出）。
- G1 设计：`docs/02-architecture.md`（四层架构 + AD-0001~0004 + 复用举证）、`docs/03-design.md`（manifest/layout/生成器/6 skill/记忆 schema/10 测试用例），approved。
- G2 实现：
  - `plugin.manifest.yaml` 单一源（6 skill + 5 宿主声明）
  - `templates/` 6 份宿主无关 skill 正文（doc-driven/gate/verify/review/no-fake-test/memory-protocol）
  - `hosts/{reasonix,claude}/layout.json` 宿主适配片段
  - `scripts/generate.py`（单一源 → dist/<host>/ 镜像，纯标准库）
  - `scripts/drift_check.py`（一致性校验，0=一致/1=漂移）
  - `scripts/install.py` / `uninstall.py`（可逆安装：快照 + 备份 + 恢复，AC-5）
  - `tests/test_plugin.py`（UT-1~4，9 用例全绿）
- 决策记录：AD-0001 单一源+生成器 / AD-0002 知识剥离+宿主记忆 / AD-0003 MVP 宿主范围 / AD-0004 纪律 skill 对齐蓝本。

### 变更
- README 覆盖模板占位（快速开始 / 开发命令 / 新增宿主步骤 / 知识剥离说明）。
- `docs/04-tasks.md`：任务拆分 TASK-0001~0008，全部实现并勾选；G3 验收通过后状态 → implemented。

### 修复
- `generate.py` 占位符渲染：`string.Template` 不认 `{{}}`，改为显式替换。
- `install.py` 复制路径：保留顶层目录名（`.reasonix`），备份/卸载路径统一相对 target。
- `install.py`/`uninstall.py`：卸载清单按宿主分文件（`.ddd-agent-plugin-manifest-<host>.json`），修复多宿主互相覆盖（真机验证发现）。
- `uninstall.py`：空目录清理改为先收集再自底向上删除，修复 `.reasonix` 空目录残留（真机验证发现）。
