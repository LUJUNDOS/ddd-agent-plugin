---
status: approved
title: 01-requirements
layer: 01
related: [00-vision]
---

# 01-requirements —— ddd-agent-plugin SRS

> 依据 00-vision。每条需求标来源与优先级（P0=MVP 必做 / P1=后续）。
> 来源：V=用户亲口 / A=Agent 推断 / I=行业默认（插件经理方法论的要求标注法）。

## 0. 调研依据（2026-08-13 法庭式对抗选型）

- **现有方案调研**：`docs/research/competitors.md`（GitHub API + 官方 README 实证）
  - 市场已由 get-shit-done（64.7k⭐）验证需求，但该项目 2026-05 已归档（头部真空）
  - 主流方案全部单宿主绑定 Claude Code；"可拔插 + 知识剥离 + 宿主记忆自进化"组合**无人做**
  - MCP memory server 提供跨宿主记忆范式，作为"记忆规程"对齐参照
- **对抗判决**：`docs/research/selection-ddd-agent-plugin.md`（B 自建胜出，30/35 vs A 17/35）
  - 自建方向确认；不复制现有方案内容，结构参照蓝本已验证纪律 skill
  - 缺陷缓解：单一源防漂移 + 真机逐宿主验证 + MVP 缩至 2 宿主

## 1. 功能需求（FR）

| ID | 需求 | 来源 | 优先级 |
|----|------|------|--------|
| FR-001 | **单一源**：插件全部内容以单一 `manifest` + 模板维护，宿主差异仅在格式层 | V | P0 |
| FR-002 | **生成器**：`generate.py` 从单一源生成各宿主镜像（MVP：reasonix、claude） | V | P0 |
| FR-003 | **一致性校验**：生成后 diff 检测漂移（drift check），非零即报 | A | P0 |
| FR-004 | **5 个纪律 skill**：doc-driven / gate / verify / review / no-fake-test（验收标准同蓝本） | V | P0 |
| FR-005 | **记忆规程 skill**：约定"何时记 / 记什么 schema / 如何回溯"，沉淀目标=宿主原生记忆 | V | P0 |
| FR-006 | **一键安装**：`install.sh`（Windows 亦可用 PowerShell）把生成物装入目标宿主 | V | P0 |
| FR-007 | **一键卸载**：uninstall 清除宿主侧全部插件文件，宿主恢复原状 | A | P0 |
| FR-008 | **知识库剥离**：插件包内不含任何 kb/ 知识内容（零知识库负担） | V | P0 |
| FR-009 | **宿主清单**：manifest 声明支持的宿主列表与每宿主适配状态（适配/已验证） | A | P0 |
| FR-010 | **DDD 文档链**：本项目自身遵循 G0~G3 五层文档 + `ddd_gate.py` 机械校验 | V | P0 |
| FR-011 | 可选：新增宿主 = 新增 per-host 模板片段 + 真机验证，不改生成器主体 | A | P1 |
| FR-012 | **新建项目 DDD 自动引导**：bootstrap skill——用户说"新建项目"时自动初始化 DDD 文档骨架（docs/00~04）+ 询问是否启动需求调研 + 选择后当场启动流程（对齐中枢 new-project Step 9） | V | P0 |
| FR-013 | **DDD 流程角色 skill 链**：goal-creator → product-manager（00/01）→ architect（02）→ ui-designer（03）→ pm（04），各角色自动衔接闸门（G0 通过才写 02 等） | V | P0 |
| FR-014 | **scaffold.py 骨架生成**：一键生成 docs/00-vision/01-requirements/02-architecture/03-design/04-tasks 空模板（frontmatter + 章节），自动化代替手动初始化 | A | P0 |
| FR-015 | **references 打包**：角色 skill 依赖的方法论文档（adversarial-selection / pm-thinking-guide / code-review-standard）随插件分发，装到宿主后引用闭环（可拔插不依赖中枢） | V | P0 |

## 2. 非功能需求（NFR）

| ID | 需求 | 度量 |
|----|------|------|
| NFR-01 | **宿主无关**：交付物为纯 markdown + 纯 Python（无第三方依赖） | 目标宿主不安装任何额外运行时 |
| NFR-02 | **可逆性**：卸载后宿主 skill 目录与安装前逐字节一致 | uninstall 后 diff 为空 |
| NFR-03 | **可扩展**：新增宿主不动生成器主体 | 只加 per-host 模板 + manifest 条目 |
| NFR-04 | **闸门防绕过**：机械校验 exit 1 即拦，不依赖 AI 自觉 | ddd_gate.py 复用 |
| NFR-05 | **文档即契约**：skill 只写目标/标准/验收，过程交模型发挥 | 对齐蓝本纪律 skill 范式 |

## 3. 验收标准（G3 对照）

| ID | 验收标准 | 验证方式 |
|----|---------|---------|
| AC-1 | 单一源生成 reasonix + claude 两宿主镜像，drift 校验 0 差异 | `python generate.py` + `drift_check` 非零即 FAIL |
| AC-2 | Reasonix 真机：安装后 5 个纪律 skill 可被正确触发 | 真机逐 skill 触发验证 |
| AC-3 | Claude Code 真机：同上（一个宿主过了不能替另一个背书） | 真机逐 skill 触发验证 |
| AC-4 | 剥离验证：插件包内无 kb/ 内容；记忆规程指向宿主原生记忆 | 包内容清单检查 + 规程文件断言 |
| AC-5 | install 一键装、uninstall 后宿主目录与安装前 diff 为空 | 安装前快照 vs 卸载后快照 |
| AC-6 | 本项目自身 DDD 门禁全绿 | `ddd_gate.py gates` PASS + 用户 Oracle 确认 |
| AC-7 | 任一宿主装上后，ddd_gate 机械闸拦截生效（未 approved 写码被拦） | 模拟违规场景真机验证 |
| AC-8 | 新建项目自动引导：装插件后对"新建项目"触发 bootstrap，自动生成 docs/00~04 骨架 + 引导需求调研启动 | 真机模拟"新建项目"流程 |
| AC-9 | 角色 skill 链可用：product-manager 等 5 角色 skill 装进宿主后可被触发，references 引用闭环（无外部依赖断链） | 真机触发 + 引用路径检查 |

## 4. MVP 边界

- **不做**：loop 契约（C-\*/T-\*）、debug/evolve/goal skill 的完整形态（仅保留记忆规程）、MCP App / Companion Web App、任何 kb 内容。
- **宿主范围**：MVP 适配并真机验证 reasonix + claude；codebuddy / codex / cursor 等仅预留 manifest 条目（P1）。
- **知识边界**：插件不含任何领域知识；经验类内容一律写宿主原生记忆（Reasonix memory / CLAUDE.md / CodeBuddy memory）。

## 5. Ubiquitous Language（词汇表）

| 词 | 含义 |
|----|------|
| 宿主 | 能加载 skill/插件并执行 agent 任务的程序（Reasonix / Claude Code / CodeBuddy 等） |
| 单一源 | 插件唯一的事实源（manifest + 模板），各宿主镜像由生成器产出 |
| 记忆规程 | 插件内约定的记忆 schema 与时机规则（不含记忆内容本身） |
| 纪律 skill | 只声明验收标准、约束 agent 行为的 skill（doc-driven/gate/verify/review/no-fake-test） |
| 真机验证 | 把插件实际装入目标宿主并真实触发验证（不是静态检查） |
