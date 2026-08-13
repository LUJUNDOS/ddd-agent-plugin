# ddd-agent-plugin —— DDD 方法论可拔插 Agent 插件

> 以 `Projects_dev` 中枢为蓝本的可拔插 Skill Plugin：**装上 = 任何 agent 获得 DDD G0~G3 闸门纪律；拔下 = 宿主无残留；经验自进化沉淀在宿主原生记忆（插件零知识库负担）。**

## 特性

| 特性 | 说明 |
|------|------|
| 🔌 可拔插 | `install.py` 一键装 / `uninstall.py` 一键卸（卸载后宿主与安装前逐字节一致） |
| 🧩 任意宿主 | 单一源 manifest + 生成器：MVP 已验证 reasonix + claude，其余宿主加一段 layout 即可 |
| 🆕 自动引导 | `bootstrap` skill：新建项目自动生成 docs/00~04 骨架 + 引导需求调研，直接走 DDD 流程（自动代替手动） |
| 👥 角色流程链 | `goal-creator` → `product-manager`（00/01）→ `architect`（02 四维调研+对抗选型）→ `ui-designer`（03）→ `pm`（04），闸门自动衔接 |
| 📐 DDD 方法论 | 6 个纪律 skill：`doc-driven`（闸门）/ `gate`（结构闸）/ `verify`（行为真证）/ `review`（收口）/ `no-fake-test`（测试真实性）+ 机械闸 |
| 🧠 知识剥离 | 插件不携带任何 kb 内容；`memory-protocol` skill 约定"何时记/记什么/如何回溯"，经验写入宿主原生记忆（Reasonix memory / CLAUDE.md） |
| 📚 自带方法论 | `references/` 打包 3 份方法论文档（法庭式对抗 / PM 思考 / 代码审查标准），装到宿主后引用闭环 |

## 快速开始

```powershell
# 1. 生成镜像（dist/<host>/）
python scripts/generate.py

# 2. 安装到宿主项目（装到 <target>/.reasonix/skills/ 或 <target>/.claude/skills/）
python scripts/install.py --host reasonix --target <你的项目目录>
python scripts/install.py --host claude   --target <你的项目目录>

# 3. 卸载（宿主恢复原状）
python scripts/uninstall.py --host reasonix --target <你的项目目录>
```

## 开发命令

```powershell
python scripts/generate.py                    # 重新生成全部宿主镜像
python scripts/drift_check.py                 # 一致性校验（0=一致 / 1=漂移）
python tests\test_plugin.py                   # 单元测试（9 用例）
python scripts/ddd_gate.py gates docs         # DDD 闸门链
python scripts/ddd_gate.py check-tasks docs   # 任务勾选核对
```

## 目录结构

```
plugin.manifest.yaml      单一源：元数据 + skill 清单 + 宿主声明
templates/                6 份宿主无关 skill 正文（{{SKILL_NAME}} 占位符）
hosts/<host>/layout.json  per-host 适配（目录布局 + frontmatter 规则）
scripts/                  generate / drift_check / install / uninstall / ddd_gate
tests/                    单元测试（UT-1~4，纯标准库 unittest）
docs/                     本项目自身 DDD 文档链（00~04 + research/）
dist/                     生成产物（不入库）
```

## 新增宿主（P1 扩展）

1. 建 `hosts/<name>/layout.json`（参照 `hosts/claude/layout.json`：base_dir / skill_dir / skill_file / frontmatter）
2. `plugin.manifest.yaml` 的 `hosts` 加条目：`<name>: { status: verified, layout: hosts/<name>/layout.json }`
3. 真机验证（AC-2/3 铁律：一个宿主过了不能替另一个背书）

## 知识剥离说明（AD-0002）

插件**不建 kb、不存经验**。动态经验（错误复盘/决策/洞察）按 `memory-protocol` skill 的 schema 写入宿主原生记忆：
- Reasonix → memory 工具 / 伴生 memory.md
- Claude Code → CLAUDE.md 追加 + memory/ 目录

拔掉插件不带走经验（特性），装上插件即恢复规程。

## 许可

MIT。以 `Projects_dev` 蓝本纪律 skill 内容为基准（AD-0004），结构对齐社区 SDD 插件范式（`docs/research/competitors.md`）。
