# methods/doc-driven-dev.md —— 文档驱动开发（DDD）

> Source of Truth。本文件是 `AGENTS.md` §1 的详细规程。代码不得凌驾文档：docs/ 比 src/ 权威。

## 1. 事实链（五层）
```
00-vision（愿景/SRS 上游）
   → 01-requirements（SRS：需求+验收标准）
   → 02-architecture（ADD：架构+ADR）
   → 03-design（详细设计）
   → 04-tasks（任务拆分 T-0001..）
```
- 上层是下层依据；下层不得与上层 `approved` 冲突。
- 每篇 `status: draft|review|approved|implemented|deprecated`。

## 2. 四道闸门（G0~G3）
| 闸门 | 放行条件 | 机械层校验 |
|------|----------|------------|
| G0 立项 | 00/01 `approved` 才写 02 | `ddd_gate.py gates` |
| G1 设计 | 02/03 `approved` 才拆 04/写码 | `ddd_gate.py gates` |
| G2 编码 | 每任务前核 03-design `approved` | `ddd_gate.py check-module` / `pre-commit` |
| G3 验收 | 对照 01 验收标准全绿才 `done` | 验证器 + 用户 Oracle |

## 3. 闸门如何真卡住（三层强制，见 AGENTS.md §1）
1. **机械层** `scripts/ddd_gate.py`：读 frontmatter `status` 静态校验链序，pre-commit / CI / VS Code 任务三层触发，`exit 1` 即拦。
2. **AI 纪律层**：写码前拿 docs 拷问实现是否偏离；CLAUDE.md 以 MUST 写死。
3. **人工层**：`approved` 由人点；实现发现设计问题 → 禁改码将就 → 回 docs 改（重评审）→ 继续。

## 4. ADR（架构决策记录）
`02-architecture.md` 内每条重大决策记 ADR：`## ADR-0001 选 SQLite` + 背景/决策/后果/状态。错误复盘可 `related: ADR-xxx` 反向追溯。

## 5. Ubiquitous Language
`docs/glossary.md`：领域术语 → 代码映射，新人/agent 共享语言。

## 6. TDD 为 G2 默认反馈环
复杂任务执行代理先写失败测试（RED）→ 最小实现（GREEN）→ 重构；验证器核对测试全绿方过 G3。

## 7. 与 Loop 衔接
`04-tasks.md` 每任务 = 一份 `tasks/T-<id>.md` 目标文档，交 Loop Engineer 执行（gate=G2/G3）。

## 8. 文档模板（frontmatter 必含）
```yaml
---
status: draft            # draft|review|approved|implemented|deprecated
title: 01-requirements
layer: 01
related: [00-vision]
---
```
