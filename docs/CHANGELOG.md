# CHANGELOG

## [0.2.0] - 2026-08-13

### 新增（中枢同步）
- 需求 FR-012~015 + 验收 AC-8/9（`docs/01-requirements.md`）：新建项目 DDD 自动引导 / 角色 skill 链 / scaffold 骨架生成 / references 打包。
- 设计（`docs/03-design.md` §11~14）：bootstrap skill 流程、5 角色 skill 规格、references 打包、scaffold.py 接口。
- 任务 TASK-0009~0013（`docs/04-tasks.md`）。
- 实现：
  - `templates/bootstrap.md`：新建项目 DDD 自动引导（对齐中枢 new-project Step 9，宿主无关询问机制）。
  - `templates/{goal-creator,product-manager,architect,ui-designer,pm}.md`：5 角色流程 skill（从中枢 `.workbuddy/skills/` 提取，宿主无关化：`methods/`→`references/`、去 `/goal`/`CLAUDE.md §` 引用、frontmatter 参数化）。
  - `scripts/scaffold.py`：一键生成 docs/00~04 骨架（幂等，纯标准库）。
  - `references/`：打包 adversarial-selection / pm-thinking-guide / code-review-standard 3 份方法论。
  - `plugin.manifest.yaml`：skills 6→12、scripts +scaffold.py、references 声明；`generate.py` 纳入 references 拷贝。
  - `tests/test_plugin.py`：UT-5（scaffold 幂等）、UT-6（references 闭环），13 用例全绿。

### 修复（v0.2.0 真机验证发现）
- `install.py`/`uninstall.py`：备份目录按宿主分文件（`.ddd-agent-plugin-backup-<host>`），修复多宿主 install 的 backup 互相覆盖导致卸载无法恢复（manifest 分宿主的同源遗漏；真机验证抓出）。
- 回归测试：`TestMultiHostRoundtrip`（同 target 双宿主装→卸→全部恢复），14 用例全绿。
- 任务 TASK-0009~0013 全部勾选（validations/run-3.md 验收记录）。

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
- `docs/04-tasks.md`：任务拆分 TASK-0001~0008（checkbox 格式对齐 check-tasks），全部实现并勾选；G3 验收通过后状态 → implemented。

### 修复
- `generate.py` 占位符渲染：`string.Template` 不认 `{{}}`，改为显式替换（保持 03-design 字面一致）。
- `install.py` 复制路径：保留顶层目录名（`.reasonix`），备份/卸载路径统一相对 target。
- `install.py`/`uninstall.py`：卸载清单按宿主分文件（`.ddd-agent-plugin-manifest-<host>.json`），修复多宿主安装互相覆盖清单（真机验证发现）。
- `uninstall.py`：空目录清理改为先收集再自底向上删除，修复 `.reasonix` 空目录残留（真机验证发现）。
