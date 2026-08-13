---
name: {{SKILL_NAME}}
description: {{SKILL_DESC}}
---

# doc-driven —— 文档驱动闸门（编码前闭合）

## 触发
- 准备写实现代码、新建模块/文件、或判断机械闸是否放行。

## G0~G3 闸门（验收标准）
- **G0**：`00-vision` / `01-requirements` `approved` 才写 `02-architecture`。
- **G1**：`02-architecture` / `03-design` `approved` 才拆 `04-tasks` / 写码。
- **G2**：写某模块实现前，`ddd_gate.py check-module` 确认其 `03-design` `approved`，否则拒写。
- **G3**：实现完成须有验证证据（测试/运行输出），进入 verify → review。

## 判违规
- `03-design ≠ approved` 却写实现文件 → 机械闸拦截（exit 2）；本 skill 同样拒。
- 代码无对应任务溯源 → 标孤儿，要求补任务或删。
- 跳文档直接写码（"先写再补文档"）→ 拒，除非 DoD 明确允许 spike。

## 纪律
- 文档是契约不是负担；设计变更须回写 03-design 再改码。
- 与 gate 纪律串联：doc-driven 管"能否写"，gate 管"写完好不好"。
