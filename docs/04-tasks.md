---
status: implemented
title: 04-tasks
layer: 04
related: [03-design]
---

# 04-tasks —— ddd-agent-plugin 任务拆分

> 依据 03-design（approved）。每任务可独立运行、独立验收（竖切不分层）。
> 勾选规则：实现+验证通过后改 `[x]`；check-tasks 核对 validations/tasks/logs 证据。

- [x] **TASK-0001** 插件骨架 + plugin.manifest.yaml
  - **内容**：建 `plugin.manifest.yaml`（03-design §2 schema：id/version/skills×6/hosts 声明），建 `templates/`、`hosts/`、`dist/` 骨架。
  - **DoD**：yaml 可解析；skills 6 项、hosts 含 reasonix/claude 声明 verified、codebuddy retired、codex planned。

- [x] **TASK-0002** templates/ 6 份 skill 正文
  - **内容**：`templates/{doc-driven,gate,verify,review,no-fake-test,memory-protocol}.md`（03-design §5：frontmatter + 验收标准，结构对齐蓝本）。
  - **DoD**：每份含 `{{SKILL_NAME}}`/`{{SKILL_DESC}}` 占位符 + 验收标准清单；memory-protocol 含记忆 schema（error/decision/insight）。

- [x] **TASK-0003** hosts/ 适配片段
  - **内容**：`hosts/reasonix/layout.json` + `hosts/claude/layout.json`（03-design §3 schema）。
  - **DoD**：json 合法；字段齐全（base_dir/skill_dir/skill_file/frontmatter）。

- [x] **TASK-0004** scripts/generate.py
  - **内容**：读 manifest × templates × layout → 生成 `dist/<host>/skills/<id>/SKILL.md` + 拷贝 ddd_gate.py；纯标准库。
  - **DoD**：`python scripts/generate.py` 生成 dist/reasonix + dist/claude；两次生成产物逐字节一致（UT-1）。

- [x] **TASK-0005** scripts/drift_check.py
  - **内容**：重新生成并与现有 dist 对比，输出漂移报告；退出码 0=一致 / 1=漂移（UT-2）。
  - **DoD**：篡改 dist 镜像后 drift_check 检出非零。

- [x] **TASK-0006** scripts/install.py + uninstall.py
  - **内容**：install 复制镜像到宿主 skill 目录 + 写 manifest-installed.json；uninstall 按清单删除（UT-3）。
  - **DoD**：install→uninstall 后宿主目录与安装前快照 diff 为空（AC-5）；幂等。

- [x] **TASK-0007** 单元测试 UT-1~4
  - **内容**：按 03-design §10 写 `tests/test_plugin.py`（纯标准库 unittest）：generate 幂等 / drift 检出 / install-uninstall 可逆 / 包内无 kb（UT-4）。
  - **DoD**：`python tests/test_plugin.py` 9 用例全绿。

- [x] **TASK-0008** README + 镜像打包 + CHANGELOG
  - **内容**：`README.md`（安装/卸载/生成/新增宿主步骤）；CHANGELOG.md；确认镜像含 ddd_gate.py。
  - **DoD**：README 覆盖 AC-5 用户路径；CHANGELOG 有记录（check-changelog 通过）；ddd_gate.py 在 dist 镜像内。

## v0.2.0（中枢同步：新建项目 DDD 自动引导 + 角色 skill 链，FR-012~015）
- [x] **TASK-0009** references/ 打包（FR-015）
  - **内容**：复制中枢 `methods/{adversarial-selection,pm-thinking-guide,code-review-standard}.md` 到 `references/`；生成器将其纳入 dist 镜像。
  - **DoD**：3 份文件存在；generate 后 dist/<host>/references/ 含 3 份（UT 断言）。

- [x] **TASK-0010** scripts/scaffold.py（FR-014）
  - **内容**：按 03-design §14 生成 docs/00~04 骨架；幂等（已存在跳过）；纯标准库。
  - **DoD**：空项目生成 5 份文档（frontmatter 合法、可过 ddd_gate gates draft 态）；重复执行不覆盖（UT）。

- [x] **TASK-0011** templates/bootstrap.md（FR-012/AC-8）
  - **内容**：新建项目自动引导 skill（03-design §11）：scaffold 骨架 → 三选项询问 → 选 A 当场启动 product-manager。
  - **DoD**：流程完整；宿主无关（询问机制通用描述）；manifest 注册。

- [x] **TASK-0012** 5 个角色 skill 模板（FR-013/AC-9）
  - **内容**：从中枢 `.workbuddy/skills/` 提取 goal-creator/product-manager/architect/ui-designer/pm，宿主无关化 + 参数化 frontmatter，references 引用改 `references/<file>`。
  - **DoD**：5 份模板；角色内引用路径指向 references/（可达断言）；闸门衔接逻辑保留。

- [x] **TASK-0013** manifest 更新 + 测试扩展 + 收口
  - **内容**：manifest skills 6→12、scripts +scaffold.py、references 声明；tests 加 UT-5（scaffold 幂等）/UT-6（references 打包）；README/CHANGELOG 更新。
  - **DoD**：generate 全量通过；drift 0 差异；测试全绿；真机模拟"新建项目"引导（AC-8）与角色 skill 引用可达（AC-9）。

## v0.2.1（中枢同步审计修复：debug + doc-driven-dev + hooks，FR-015 扩展）

- [x] **TASK-0014** debug skill + doc-driven-dev 打包
  - **内容**：提取中枢 debug skill（宿主无关化）→ templates/debug.md；doc-driven-dev.md 进 references/；manifest skills 12→13。
  - **DoD**：纪律层 6/6；references 4 份；测试断言更新。

- [x] **TASK-0015** hooks 自动挂载
  - **内容**：hosts layout 增 hooks 字段；install 合并写宿主 settings.json（保留原 hooks/先备份）；uninstall 恢复/删除；claude_gate_hook.py 加回 scripts/。
  - **DoD**：TestHooks 双场景（保留原 hook/创建-删除）；卸载后 settings.json 与安装前一致。

## v0.2.2（自进化：evolution-scan，FR-016/AC-10）

- [x] **TASK-0016** evolution-scan skill
  - **内容**：templates/evolution-scan.md（长期区维护：退休 30 天/合并去重/冲突检测/跨项目提炼；去初版 ≥3 次重复，晋升归 memory-protocol）；manifest skills 13→14。
  - **DoD**：镜像 14 skill 渲染正确（无 ≥3 次提炼逻辑残留）；memory-protocol ↔ evolution-scan 双向引用；AC-10 真机模拟。

## v0.2.3（设计能力融合：FR-017/018/AC-11）

- [x] **TASK-0017** 设计能力融合
  - **内容**：references 3 子目录（design-dna 全量 5 份 / finesse-ui 精选 13 份 / finesse-brief 核心 5 份 + README 来源说明）；ui-designer 增强（DNA/高工艺/反廉价审计）+ pm/architect 共享引用；generate 递归拷贝；manifest version 0.2.3。
  - **DoD**：镜像子目录可达（AC-11）；无 html/js 资产；引用闭环含子目录；16 测试全绿；manifest version 0.2.3。

## v0.2.5（调度传动：goal-executor，FR-019/AC-12）

- [x] **TASK-0018** goal-executor 调度传动
  - **内容**：templates/goal-executor.md（自驱循环/并行 worktree/重试停滞/active-goal 恢复/verifier 子代理指引）；memory-protocol 加 active-goal 事件；hosts agents 声明 + verifier 定义（claude .claude/agents/verifier.md / reasonix task-spawn）；generate 拷贝 agents；manifest skills 15 + version 0.2.5。
  - **DoD**：15 skill 入镜像；claude verifier agent 可达；drift 0；16 测试全绿；AC-12 真机模拟（循环/恢复/并行指引完整）。
