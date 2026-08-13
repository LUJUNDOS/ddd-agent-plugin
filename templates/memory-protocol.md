---
name: {{SKILL_NAME}}
description: {{SKILL_DESC}}
---

# memory-protocol —— 知识库剥离的记忆规程

> 本插件不携带任何知识库（kb）内容（AD-0002）。动态经验按本规程沉淀到**宿主原生记忆**：
> reasonix → memory 工具 / 伴生 memory.md；claude → CLAUDE.md 追加 + memory/ 目录。
> 对齐范式：MCP memory server 的"身份/行为/偏好/目标/关系"分类。

## 何时记（触发事件）
1. **error**：踩坑并定位根因（报错信息 + 根因 + 修复 + 验证方式）。
2. **decision**：做了影响后续开发的取舍（上下文 + 选项 + 选择 + 理由）。
3. **insight**：发现可复用的经验/模式（主题 + 结论 + 适用场景）。

## 记什么（schema）
```yaml
error:    { symptom, root_cause, fix, verified_by, date }
decision: { context, options, chosen, rationale, date }
insight:  { topic, takeaway, applies_to }
```

## 如何回溯（验收标准）
- 新会话开头检索宿主记忆中的 error / decision 类型，命中先读再动手。
- 同类 error 第二次出现：若记忆中有 fix，直接复用，不重复诊断。
- 同类事件发生 ≥3 次：视为该宿主环境的高频模式，写入宿主记忆的长期区（如 CLAUDE.md 固定条目）。
- 长期区条目的维护（退休/合并/冲突/跨项目提炼）由 `evolution-scan` 负责（本 skill 只做记与晋升，不越权维护）。

## 判违规
- 把经验写回插件包内（kb/ 或 templates/）→ 拒。插件是稳定规程，不是存储。
- 记了 error 却没记 verified_by / fix → 视为未闭环，补全。

## 纪律
- 记忆在宿主，规程在插件；拔掉插件不带走经验，装上插件即恢复规程。
- 记忆要原子（一条事实一条记录），可独立增删。
