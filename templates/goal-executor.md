---
name: {{SKILL_NAME}}
description: {{SKILL_DESC}}
---

# goal-executor —— 调度传动（自动跑完一个目标）

> 把 5 个领域工位（goal-creator → product-manager → architect → ui-designer → pm）自动串联成自驱循环。**不新增领域角色**——主 agent 兼任调度（orchestrator 心态），工位切换即戴对应角色帽。

## 触发
- 用户说"帮我做 XX""实现这个目标""跑完这个流程""开始做"等目标启动意图时自动接管。
- 新会话开头若记忆命中 `active-goal` → 自动进入恢复模式（见"跨会话恢复"）。

## 单任务模式（验收标准）
1. **启动**：读宿主记忆检索 `active-goal`。
   - 有 → 恢复：读取 current_stage / next_action，从断点继续（不重跑已完成工位）。
   - 无 → 新建：目标标准化（goal-creator）→ 写入 active-goal（goal/current_stage/next_action/blockers）。
2. **工位循环**（顺序：product-manager → architect → ui-designer → pm）：
   - 戴对应角色帽执行（读该角色 skill 的验收标准）。
   - 每个工位产出后：`ddd_gate.py gates docs --strict` 自查（该层 approved 前置闸）。
   - 验证：优先 spawn verifier 子代理（独立上下文，只持 DoD + 产出）；宿主不支持子代理时退化为 verify 纪律自律。
   - 通过 → 更新 active-goal（current_stage=下一工位，next_action=具体动作）→ 进入下一工位。
   - 失败 → 记录负面（memory-protocol error）→ 重试 ≤3 次（同一类改法不重复）→ 仍失败 → 停，报阻塞（blockers 写回 active-goal）。
3. **执行层**：pm 拆出的任务逐任务执行（TDD：先红后绿），每任务过 gate（check-module + 测试）。
4. **收口**：全部工位完成 → 产出收口报告（完成清单/验证证据/遗留），清除 active-goal（标记 done）。

## 并行模式（验收标准）
- pm 拆出的任务含**可并行组**（文件/模块无交叉）。
- 对并行组：`git worktree add <path> -b <branch>` 每任务独立 worktree → 宿主并行 spawn executor（每子代理一个 worktree）→ 全部完成 → 逐个验证 → `git merge --ff-only` + `git worktree remove`。
- 冲突规避（硬规则）：**两任务必改同一文件 → 串行**（并入主序列），不得并行。
- 并行组在 active-goal 中标注（current_stage 含并行子状态）。

## 跨会话恢复（验收标准）
- 每工位完成时更新 active-goal（写宿主记忆，memory-protocol 的 active-goal 事件）。
- 新会话：记忆检索命中 active-goal → 自动恢复（或用户说"继续"）→ 从断点续跑。
- active-goal 含 blockers 且非空 → 恢复时先报告阻塞原因，不盲目重试。

## 循环控制（三道刹车精简版）
- **重试上限**：同一工位/任务连续失败 ≤3 次（复用 debug 纪律的负面记录 + 3 连败即停），超出即停报阻塞。
- **max_iter**：单个目标最多 N 轮（默认 10），超出停止。
- **停滞检测**：连续 2 轮无实质进展（测试 delta=0 / 无新产出）→ 停，升级给用户。

## 判违规
- 工位产出未过 ddd_gate 自查就进入下一工位 → 违规。
- 并行组未做文件冲突判定就并行 → 违规。
- 验证环节由实现者同上下文自验且未 spawn 子代理（宿主支持时）→ 违规。
- 3 连败后仍盲目第 4 次重试 → 违规。

## 纪律
- 主 agent 是调度（orchestrator 心态），工位执行戴对应角色帽——不要在一个工位里做下一个工位的事。
- 与 verify/review 串联：gate（结构）→ verify（行为，优先子代理）→ review（收口）。
- 与 memory-protocol 串联：每工位完成更新 active-goal；失败记录 error；收口清除。
- 与 debug 串联：重试循环用负面记录 + 3 连败即停。
