---
name: {{SKILL_NAME}}
description: {{SKILL_DESC}}
---

# evolution-scan —— 记忆进化扫描（扫描式自进化）

> 与 memory-protocol 分工：memory-protocol 管"记"（何时记/记什么/如何回溯，**不改变**）；本 skill 管"扫/提炼/晋升/退休"。

## 触发
- 用户说"进化扫描""看看记住了什么""沉淀经验""扫描记忆"等意图时自动加载。
- 里程碑/阶段完成后（可选周期触发）。

## 职责（验收标准）
1. **扫描**：读宿主原生记忆中的 error / decision / insight 条目（Reasonix memory / CLAUDE.md / memory 文件）。
2. **提炼**：
   - 同类 error 出现 ≥3 次且 fix 已验证 → 提炼为经验规则（symptom + root_cause + fix + verified_by）。
   - 同类 decision 出现 ≥3 次 → 提炼为默认决策原则（context + chosen + rationale）。
   - insight 跨项目通用 → 保留为可复用要点。
3. **晋升**：提炼结果写入宿主记忆**长期区**（如 CLAUDE.md 固定条目），每条带 `created` 日期 + 触发计数（`hits`）。
4. **退休（30 天规则）**：
   - 长期区条目 `created` 或最近 `hits` 更新距今 > 30 天、且期间无新 error/decision 命中 → 标**退休候选**。
   - 退休候选**必须经用户确认**后才清理/归档（用户 Oracle 不可跳过）。
5. **报告**：输出本次扫描的提炼清单 / 晋升清单 / 退休候选清单（含理由），逐项可核。

## 判违规
- 扫描结束不产出三份清单（提炼/晋升/退休）→ 违规。
- 退休条目未经用户确认直接删除 → 违规。
- 修改 memory-protocol 的"记"机制（何时记/记什么 schema）→ 违规（本 skill 只读扫描 + 提案，不接管记录）。
- 晋升条目不带 created/hits 元数据 → 违规（退休规则依赖时间戳）。

## 纪律
- 只读宿主记忆 + 写提案；写长期区（晋升）与清理（退休）均须用户确认。
- 与 memory-protocol 串联：记（protocol）→ 扫/提炼/晋升/退休（scan），两 skill 互不越权。
- 高频模式（≥3 次）是晋升信号；30 天无触发是退休信号——双向进化，避免记忆膨胀。
