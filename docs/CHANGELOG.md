# CHANGELOG

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
- `docs/04-tasks.md`：任务拆分 TASK-0001~0008（checkbox 格式对齐 check-tasks），全部实现并勾选。

### 修复
- `generate.py` 占位符渲染：`string.Template` 不认 `{{}}`，改为显式替换（保持 03-design 字面一致）。
- `install.py` 复制路径：保留顶层目录名（`.reasonix`），备份/卸载路径统一相对 target。
