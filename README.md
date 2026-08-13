# <项目名> —— 项目脚手架（复制自 Projects_dev/projects/_template）

本目录是从中枢 `_template` 复制的新项目骨架。源码在 `src/`，文档在 `docs/`（DDD Source of Truth），执行日志在 `tasks/logs/`，运行时契约在 `contracts/`（`/goal` 按需生成），验证证据在 `validations/`。共享契约模板在根目录 `contracts/_templates/`。

## 目录
| 路径 | 作用 |
|------|------|
| `src/` | 源码（执行代理经 git worktree 隔离写码） |
| `docs/` | DDD 五层事实链 00~04（比代码权威） |
| `tasks/` | 下层任务 `T-<id>.md` + `logs/` |
| `contracts/` | 运行时 Loop 契约 `C-<id>.md`（`/goal` 按需生成；默认模板在根目录 `contracts/_templates/`） |
| `validations/` | 验证器证据（PR 评论/Checks） |
| `scripts/` | harness：`ddd_gate.py` `kb_lint.py` `drift_check.py` |
| `.vscode/` | VS Code 任务/扩展（跑闸门+测试） |
| `.claude/` `.codebuddy/` | Claude Code / CodeBuddy 双 Agent 入口 |

## 闸门
写码前 `python scripts/ddd_gate.py check-module docs --module <path>`；commit 前 Hook 自动跑 `ddd_gate` pre-commit。

## 命令（需中枢 ~/.workbuddy/skills 已装）
`/goal` `/ingest` `/evolve` `/new-project`（本项目已存在，用 `/goal` 立目标）。
