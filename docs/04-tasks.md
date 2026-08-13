---
status: draft
title: 04-tasks
layer: 04
related: [03-design]
---

# 04-tasks —— ddd-agent-plugin 任务拆分

> 依据 03-design（approved）。每任务可独立运行、独立验收（竖切不分层）。
> 勾选规则：实现+验证通过后改 `[x]`；check-tasks 核对 validations/tasks/logs 证据。

- [x] **TASK-0001** 插件骨架 + plugin.manifest.yaml
  - **内容**：建 `plugin.manifest.yaml`（03-design §2 schema：id/version/skills×6/hosts 声明），建 `templates/`、`hosts/`、`dist/` 骨架。
  - **DoD**：yaml 可解析；skills 6 项、hosts 含 reasonix/claude 声明 verified、codebuddy/codex planned。

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
