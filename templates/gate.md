---
name: {{SKILL_NAME}}
description: {{SKILL_DESC}}
---

# gate —— 提交前自检（硬闸包装）

## 触发
- 提交、合并分支、或宣称"闸门通过"之前。

## 程序
1. **文档闸门链路**：`python scripts/ddd_gate.py gates docs`
   - 校验 00~04 状态链（approved 前置），链路闭合才放行。
2. **模块写码前**：`python scripts/ddd_gate.py check-module docs --module <path>`
   - 确认对应 03-design `approved`，否则拒写（与机械 hook 一致）。
3. **不变量漂移**：`python scripts/drift_check.py`
   - 检测契约/任务状态不一致、镜像漂移等。

## 判 FAIL
- 任一命令 exit ≠ 0 → 拦截，输出具体哪道闸、哪个文件、哪条规则。
- 不得用 `--force` 绕过；确需例外由人显式批准并记录。

## 纪律
- 闸门是硬约束，不是建议；红即停，修完重跑。
- 本 skill 不替代 verify（验证）与 review（收口），三者串联：gate（结构）→ verify（行为）→ review（收口）。
