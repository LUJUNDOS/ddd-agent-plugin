> **本文件为中枢 `methods/performance-optimization.md` 的打包参考（随 ddd-agent-plugin 分发）。**
> 定位：**技术参考层**（性能排查方法），区别于插件的流程/纪律类方法论（DDD 闸门、代码审查等）。
> 适用：agent 遇到性能场景（API 延迟/SQL 变慢/CPU 内存异常/bundle 过大）时的排查框架。

# 性能优化方法论（Performance Optimization）

> 状态：2026-08-13 建立。来源：path-wise `.claude/agents/performance-optimizer.md`（Claude 官方 subagents 教程示例，原文已评估：内容质量高、方法通用，收录为本方法备查）。适用范围：任何项目遇到性能场景时（API 延迟、SQL 变慢、CPU/内存异常、bundle 过大）。

## 核心原则：先量化，再优化

| 原则 | 说明 |
|------|------|
| 先界定范围 | 是 API / 数据库 / 前端 / 脚本 / 算法？别一上来就到处看 |
| 先量化，再优化 | 建立 baseline，不要凭感觉改；"感觉慢了"不是证据 |
| 找最有影响力的瓶颈 | 优化 20% 热点的收益远大于优化 80% 冷路径 |
| 一次只做一个高收益改动 | 多改动混在一起无法归因收益；逐个验证 |
| 重测并记录收益与代价 | Before/After 数字说话，Trade-offs 写清楚 |

## 五维分析清单

### 1. 算法与数据结构
- 是否存在明显 `O(n²)` 或重复遍历
- 是否能用更合适的数据结构降低查找成本（哈希表 vs 列表）
- 是否有重复计算、重复序列化、重复解析
- 是否适合缓存或 memoization

### 2. 数据库
- 是否存在 N+1 查询
- 是否缺索引（用 `EXPLAIN ANALYZE` 验证，不猜）
- 是否一次性加载了过多数据
- 是否只查了真正需要的列（避免 `SELECT *`）
- 连接复用是否合理

### 3. 后端 / API
- 重活是否卡在请求路径里（可异步化/队列化）
- 是否存在不必要的网络往返
- 是否能压缩响应或改成流式输出
- 连接池 / HTTP client / SDK 是否复用

### 4. 前端
- bundle 是否过大，能否 lazy-load
- 是否有 layout thrashing
- 高频事件是否该 debounce / throttle
- 是否适合用 Web Worker 分担 CPU 密集任务

### 5. 内存
- 是否存在泄漏风险
- 是否在热点路径频繁分配对象
- 是否该 streaming 而不是整块读入

## 常用 profiling / benchmark 命令

```bash
# Node.js CPU 性能分析
node --prof app.js
node --prof-process isolate-*.log > profile.txt

# Python 性能分析
python -m cProfile -s cumulative script.py

# Go pprof 性能分析
go test -cpuprofile=cpu.out ./...
go tool pprof cpu.out

# PostgreSQL 排查
EXPLAIN ANALYZE SELECT ...;

# Go benchmark 基准测试
go test -bench=. -benchmem ./...

# k6 负载测试
k6 run --vus 50 --duration 30s load-test.js
```

## 输出格式（每个优化项）

- **Bottleneck**：慢在哪里
- **Root Cause**：根因是什么
- **Before**：优化前指标
- **Change**：做了什么改动
- **After**：优化后指标
- **Trade-offs**：副作用或取舍

## 排查清单（自检）

- [ ] 已采集 baseline
- [ ] 已通过 profiling / metrics 找到热点
- [ ] 根因已确认，不是猜测
- [ ] 已实现优化
- [ ] 测试仍通过
- [ ] 已重新测量收益
- [ ] 已给出后续监控建议

## 与 DDD 体系的关系

| 环节 | 定位 |
|------|------|
| 触发时机 | 实现后 / 审查阶段（review skill 质量维度中性能问题按 Severity 分级：明显性能瓶颈 = High 阻塞合并） |
| 与 verify 的关系 | 性能优化前先跑 verify（行为真证），优化后再跑一次确认测试仍通过——排查清单第 5 项 |
| 与 no-fake-test 的关系 | 性能数据必须来自真实 profiling 输出，禁止"感觉快了"式断言 |

## 适用范围与限制

- **适用**：API 延迟明显偏高、SQL 查询变慢、算法/脚本 CPU 内存异常、bundle 膨胀。
- **限制**：本方法是"瓶颈定位 + 优化验证"流程，不替代架构级性能设计（那是 architect 02 阶段的事）；不追求过早优化（YAGNI）。
