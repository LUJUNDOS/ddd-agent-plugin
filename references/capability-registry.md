> **本文件为中枢 `methods/capability-registry.md` 的打包参考（随 ddd-agent-plugin 分发）。**
> 插件的能力注册表角色由 `plugin.manifest.yaml` 承担（skills/hosts/scripts/references 清单）；
> 本文件说明中枢的注册表模式与登记方法，供理解 manifest 设计意图参考。文中的中枢命令（/goal、/ingest 等）与 loop 契约引用为中枢语境，插件不提供。

# methods/capability-registry.md —— 能力资产注册表

> 登记每个 skill / agent / command 的用途、scope、被哪些 loop 契约引用。与 `event-sources.md` 同为「注册表」模式，避免能力散落。
> 契约 SOP 写 `use: skill:<name>` / `spawn: agent:<name>`，编排/执行代理据此调用。

## 1. 命令（人 → 编排代理入口，跨项目）
| capability | type | scope | 触发角色 | 引用方法 |
|-----------|------|-------|----------|----------|
| `command:/new-project` | slash | global | orchestrator | 复制 _template + git init + gh |
| `command:/goal` | slash | global | orchestrator→exec→verify | 建/更新契约→跑 loop |
| `command:/ingest` | slash | global | orchestrator→exec | 触发 C-INGEST |
| `command:/evolve` | slash | global | orchestrator | 触发 meta 契约 |
| `command:/drift` | slash | global | orchestrator | 手动 Housekeeper |
| `command:/followups` | slash | global | 人 | 看跟进看板 |
| `command:/loop-status` | slash | global | 人 | 读 loop-runs-index |

## 2. Skill（执行面能力）
| skill | scope | 被引用 | 说明 |
|-------|-------|--------|------|
| `loop-engineer` | 项目 | C-* | Loop 编排执行 |
| `doc-driven-dev` | 项目 | G0~G3 | DDD 闸门纪律 |
| `kb-ingest` | 项目 | C-INGEST | raw→wiki 提炼 |
| `kb-lint` | 项目 | C-DOCS-SWEEP | 一致性清扫 |
| `drift-check` | 项目 | C-HOUSEKEEPER | 漂移检测 |
| `proj-sync` | 项目 | C-PROJ-SYNC | 知识回流 |

## 3. Agent（常设子代理）
| agent | 职责 | 与临时 spawn 区别 |
|-------|------|-------------------|
| `verifier` | 独立上下文验证 | 每 loop 临时 spawn，不常设执行型子代理 |
| `evolution-runner` | 跑 evolve draft | 仅 evolve 时 spawn |

## 4. 双表示纪律
同一命令逻辑 Reasonix（`.reasonix/skills/`，经 ddd-agent-plugin 的 install.py 安装）与 Claude Code / Reasonix 兼容通道（`.claude/skills/`）各一份，**单一源在 `methods/`**，改一处须同步另一处（由 `/evolve` 或 Housekeeper 提示防漂移）。
> 2026-08-14：CodeBuddy 已退役（`CODEBUDDY.md` / `.codebuddy/` 不再维护），命令部署通道由 `.claude/commands/*.md` 迁移至 `.claude/skills/`（skill 化）+ `.reasonix/skills/`（Reasonix 原生）。

## 5. 新增能力步骤
1. 在 `~/.workbuddy/skills/` 或 `projects/<proj>/.workbuddy/skills/` 写薄 SKILL.md（只入口+指针，重内容放 `references/`）。
2. 本表加一行 + 绑定引用它的契约。
3. 若是命令，同步 `.claude/skills/`（Claude Code / Reasonix 兼容）+ `.reasonix/skills/`（Reasonix 原生，经 ddd-agent-plugin install.py）。
