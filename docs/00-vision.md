---
status: approved
title: 00-vision
layer: 00
related: []
---

# 00-vision —— ddd-agent-plugin：DDD 方法论可拔插 Agent 插件

## 1. 背景与问题

`Projects_dev` 中枢工作台实证了一套有效的 DDD 开发纪律：四道闸门（G0~G3）、纪律 skill（doc-driven/gate/verify/review/no-fake-test/debug）、机械层脚本（ddd_gate.py 等）。但它**绑定在中枢工作台上**：

1. **迁移成本高**：项目要用整套 DDD 方法，需要复制 `_template`、依赖中枢的 `AGENTS.md` 规则、`kb/` 知识库、`methods/` 方法论——换一个 agent 环境就要整套搬迁。
2. **知识库是负担**：`kb/` 与开发流程耦合，插件化时应剥离；动态经验（错误复盘、决策）沉淀在文件知识库里，与宿主记忆脱节。
3. **多宿主漂移**：当前 Claude Code / CodeBuddy / Reasonix 三套镜像手写维护，宿主增多后漂移成本线性增长。

## 2. 愿景

做一个**可拔插的 Skill Plugin**：

- **装上** = 任何 agent 立刻获得 DDD 开发方法论（四道闸门 + 纪律 skill + 记忆规程），不依赖中枢；
- **拔下** = 宿主恢复原状，无残留；
- **知识不进插件**：插件只携带稳定规程（DDD 规则、skill 验收标准、记忆 schema）；动态经验（项目经验、错误复盘、决策记录）**自进化沉淀在各宿主原生记忆**里；
- **单一源维护**：一份 manifest + 模板生成任意宿主镜像，防漂移。

## 3. 目标

| # | 目标 | 度量 |
|---|------|------|
| G1 | 单一源生成多宿主镜像 | MVP 验证 Reasonix + Claude Code 两个宿主，架构支持任意宿主 |
| G2 | DDD 纪律可携带 | 装上后 agent 具备 G0~G3 闸门 + 5 个纪律 skill |
| G3 | 知识库剥离 | 插件包内无 kb 内容；经验写入宿主原生记忆 |
| G4 | 可拔插 | install 一键装 / uninstall 无残留 |

## 4. 非目标（MVP 明确不做）

- **Loop 契约体系**（C-\*/T-\*、orchestrator/executor/verifier 三角色）不进插件——那是中枢专属机制，插件化价值低、复杂度高。
- **知识库内容**：不携带任何 kb/ 知识页。
- **UI**：Skill Plugin 形态，无界面、无 MCP App、无 Companion Web App。

## 5. 关键决策（可行性研究结论，2026-08-13 用户确认）

| 决策 | 结论 | 依据 |
|------|------|------|
| D1 形态 | **Skill Plugin**（无界面、装方法） | 插件经理方法论：装的是方法而非功能 |
| D2 知识剥离 | **规程固化 + 经验入宿主记忆** | 插件经理方式：稳定知识在 skill 文件本身，动态经验不沉淀在插件 |
| D3 宿主范围 | **架构全宿主 + MVP 验证 Reasonix + Claude Code** | 真机集中原则：一个宿主过了不能替另一个背书 |
| D4 适配策略 | **单一源 manifest + 生成器** | 防漂移，宿主数 ≥3 时手写镜像成本不可接受 |

## 6. 成功标准（一句话）

> 一条命令装进任一 agent，该 agent 立即获得 DDD 闸门纪律，拔掉后宿主无残留；经验自进化留在宿主记忆里，插件自身零知识库负担。
