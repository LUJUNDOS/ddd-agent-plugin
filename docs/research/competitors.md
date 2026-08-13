# docs/research/competitors.md —— 现有方案调研（四维调研·竞品形态维度）

> 调研日期：2026-08-13。方法：GitHub API 搜索 + 官方 README 抓取（附来源 URL）。
> 用途：02-architecture 的证据底座 + 法庭式对抗选型的候选清单。
> 本地对照：kb/wiki/topics/plugin-manager-harness.md（插件经理方法论）、sdd-full-chain-practice.md（SDD 全链路）。

## 1. SDD/DDD 方法论类 agent 插件

| 方案 | 形态 | 宿主 | Stars/活跃度 | 许可证 | 一句话特点 |
|------|------|------|-------------|--------|-----------|
| [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | meta-prompt + skill 包 | Claude Code | **64.7k**⭐ · **2026-05 已归档(archived)** | MIT | meta-prompting + context engineering + spec-driven development 系统 |
| [Pimzino/claude-code-spec-workflow](https://github.com/Pimzino/claude-code-spec-workflow) | workflow 包 | Claude Code | 中等 · 活跃 | — | SDD 自动化：Requirements → Design → Tasks → Implementation |
| [zhu1090093659/spec_driven_develop](https://github.com/zhu1090093659/spec_driven_develop) | skill/规则包 | **多宿主**（claude-code/codex/cursor） | 965⭐ · 2026-07 更新 | MIT | 宣称多宿主 SDD，工程网络拓扑（topics 标注） |
| [tzachbon/smart-ralph](https://github.com/tzachbon/smart-ralph) | Claude Code plugin | Claude Code | 510⭐ · 2026-07 更新 | MIT | SDD + Ralph Wiggum loop + 智能压缩 |
| [softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit) | skill 合集 | 通用 coding agent | 2316⭐ · 2026-03 | MIT | 通用 skills 精选集（dev/docs/planning） |
| [daymade/claude-code-skills](https://github.com/daymade/claude-code-skills) | skill 市场 | Claude Code | 中 · 活跃 | — | 生产级 skills 市场 |
| [athola/claude-night-market](https://github.com/athola/claude-night-market) | 23 plugins 市场 | Claude Code | 327⭐ · **2026-08 活跃** | MIT | TDD 强制 hooks + SDD + code review + lifecycle；186 skills/128 commands/54 agents |

## 2. agent 记忆 / 自进化方案

| 方案 | 形态 | 宿主 | Stars/活跃度 | 许可证 | 一句话特点 |
|------|------|------|-------------|--------|-----------|
| [@modelcontextprotocol/server-memory](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) | MCP 知识图谱记忆 | **任意支持 MCP 的宿主** | 官方 · 活跃 | MIT | entities/relations/observations 图谱；JSONL 持久化；自带"何时记/记什么"系统提示词范式 |
| [dhaupin/vant](https://github.com/dhaupin/vant) | 独立记忆运行时 | agent 框架 | 10⭐ · 2026-08 | MIT | durable AI memory + 冷存储 + **代际进化(generational evolution)** |

## 3. 调研洞察

1. **需求已验证、头部真空**：SDD/方法论类插件赛道被 get-shit-done（64.7k⭐）证明是巨大刚需，但该项目 **2026-05 已归档**——头部缺位，市场空窗。
2. **几乎全部单宿主**：主流方案都绑定 Claude Code；宣称多宿主的（spec_driven_develop）Star 量仅 965，且无"真机逐宿主验证"的证据。
3. **"可拔插 + 知识剥离 + 宿主记忆自进化"组合无人做**：规则包类（get-shit-done/spec workflow）无记忆；记忆类（MCP memory/vant）无 DDD 方法论。**本插件的差异化定位成立。**
4. **记忆规程有现成范式**：MCP memory 的 system prompt（身份/行为/偏好/目标/关系分类 + 更新流程）可作为本插件"记忆规程 skill"的对齐参照。
5. **许可证友好**：候选参照全部 MIT，可自由借鉴；但**无直接可复用的源码级资产**（都是方法论/规则文本），自建成本主要是组装而非重写。
6. **归档信号**：get-shit-done 归档可能提示"纯规则包"路线难持续——印证"知识剥离 + 记忆自进化"方向的重要性（规则会过期，记忆会生长）。

## 4. 来源清单

- GitHub API search: `spec driven development claude` / `claude code skills development workflow` / `agent memory persistence autonomous`（2026-08-13 抓取）
- modelcontextprotocol/servers src/memory/README.md（2026-08-13 抓取）
