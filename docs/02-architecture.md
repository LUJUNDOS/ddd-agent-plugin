---
status: approved
title: 02-architecture
layer: 02
related: [00-vision, 01-requirements]
---

# 02-architecture —— ddd-agent-plugin 架构

> 依据 01-requirements（FR-001~011）。上游 approved 后本层方可 approved。

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────┐
│  单一源层（唯一事实源）                                    │
│  plugin.manifest.yaml + templates/*.md（宿主无关正文）     │
├─────────────────────────────────────────────────────────┤
│  生成器层                                                 │
│  generate.py：manifest × hosts/<host>/layout → 宿主镜像    │
│  drift_check.py：镜像 vs 单一源一致性（防漂移）             │
├─────────────────────────────────────────────────────────┤
│  宿主适配层（per-host 片段，差异最小化）                    │
│  hosts/reasonix/ · hosts/claude/（目录布局 + frontmatter） │
├─────────────────────────────────────────────────────────┤
│  交付层                                                   │
│  install.py / uninstall.py：一键装/卸，可逆（AC-5）        │
└─────────────────────────────────────────────────────────┘
        │ 插件内容（5 纪律 skill + 记忆规程 + ddd_gate.py）
        ▼
┌─────────────────────────────────────────────────────────┐
│  宿主侧                                                    │
│  Reasonix：.reasonix/skills/<name>/SKILL.md               │
│  Claude Code：.claude/skills/<name>/SKILL.md              │
│  记忆沉淀 → 宿主原生记忆（Reasonix memory / CLAUDE.md）     │
└─────────────────────────────────────────────────────────┘
```

## 2. 组件职责

| 组件 | 职责 | 对应 FR |
|------|------|---------|
| `plugin.manifest.yaml` | 插件元数据：skill 清单、宿主声明（支持列表+适配状态）、版本 | FR-001/FR-009 |
| `templates/*.md.j2` | 6 份宿主无关 skill 正文（5 纪律 + 1 记忆规程） | FR-004/FR-005 |
| `hosts/<host>/layout.json` | 每宿主的目录布局与 frontmatter 格式规则 | FR-002 |
| `scripts/generate.py` | 渲染生成各宿主镜像到 `dist/<host>/` | FR-002 |
| `scripts/drift_check.py` | 生成后 diff 校验（镜像与单一源语义一致） | FR-003 |
| `scripts/install.py` | 复制镜像到目标宿主 skill 目录 + 登记清单 | FR-006 |
| `scripts/uninstall.py` | 按清单删除宿主侧文件，宿主恢复原状 | FR-007 |
| 内置 `ddd_gate.py` | 机械闸（复用蓝本，纯 Python 宿主无关） | FR-010/NFR-04 |

## 3. 关键架构决策（ADR）

### AD-0001 单一源 + 生成器（approved 依据：FR-001/002/003）
- **背景**：≥3 宿主时手写镜像漂移成本线性增长（蓝本"双表示纪律"教训）。
- **决策**：所有 skill 正文单一源 `templates/`，宿主差异收敛到 `hosts/<host>/layout.json`（目录+frontmatter 格式），`generate.py` 产出镜像，`drift_check.py` 校验。
- **后果**：新增宿主 = 加 `hosts/<host>/` 片段 + manifest 条目（FR-011 P1），不动生成器主体。

### AD-0002 知识剥离 + 宿主原生记忆（依据：FR-005/008 + 插件经理方法论 D2）
- **背景**：插件可拔插要求零状态；kb 内容会过期（get-shit-done 归档的教训），记忆会生长。
- **决策**：插件仅含稳定规程（skill 正文 + 记忆 schema）；动态经验（错误复盘/决策）按 `memory-protocol` skill 写入宿主原生记忆。对齐 MCP memory server 的"身份/行为/偏好/目标/关系"分类范式，但落点映射各宿主原生机制（Reasonix memory / CLAUDE.md），**不引入独立记忆文件**。
- **后果**：插件体积最小化；换宿主时经验留在原宿主记忆（特性而非缺陷）。

### AD-0003 MVP 宿主范围 = reasonix + claude（依据：FR-009 + 真机铁律）
- **背景**：插件经理铁律"一个宿主过了不能替另一个背书"；全宿主真机验证成本高。
- **决策**：架构按任意宿主设计（manifest 声明），MVP 真机验证 reasonix + claude；codebuddy/codex/cursor 仅 manifest 预留（P1）。
- **后果**：AC-2/3 只覆盖 2 宿主；其余宿主状态=「未适配」。

### AD-0004 纪律 skill 对齐蓝本、不发明方法论（依据：对抗判决缓解措施）
- **背景**：自研内容冷启动风险（红队 B2）。
- **决策**：5 个纪律 skill 的验收标准**结构对齐**蓝本 `_template/.claude/skills/`（已验证 1 年+），仅做宿主无关化改造（frontmatter 参数化）。
- **后果**：内容风险可控；蓝本为唯一内容基准。

## 4. 复用举证表（adversarial-selection §4 模板）

| 组件 | 复用来源 | 复用部分 | 改造量 | 工作量估算 | 风险 |
|------|---------|---------|--------|-----------|------|
| 5 纪律 skill 内容 | 蓝本 `projects/_template/.claude/skills/` | SKILL.md 正文（doc-driven/gate/verify/review/no-fake-test） | 小幅改造（frontmatter 参数化） | 0.5 人日 | 低（已验证） |
| 机械闸 | 蓝本 `scripts/ddd_gate.py` | 完整脚本 | 开箱即用（随插件分发） | 0 | 低（纯标准库） |
| 记忆分类范式 | MCP memory server system prompt | 身份/行为/偏好/目标/关系分类 | 对齐参照（不复制代码） | 0.5 人日 | 中（宿主记忆机制差异） |
| 单一源+生成器 | 无现成复用 | — | 全新开发 | 1-2 人日 | 中（模板引擎选择） |

## 5. 非功能架构约束

- **纯 Python + 纯 markdown**：无第三方依赖（NFR-01）——模板渲染用标准库 `string.Template` 而非 jinja2。
- **可逆安装**：install 写清单（`dist/<host>/manifest-installed.json`），uninstall 按清单删除（NFR-02）。
- **Windows 兼容**：脚本兼容 PowerShell 调用（蓝本 ddd_gate.py 已验证）。

## 6. 数据流

```
用户运行 install.py --host reasonix
  → generate.py 渲染 dist/reasonix/（manifest × layout）
  → 复制 .reasonix/skills/<skill>/SKILL.md
  → 写 manifest-installed.json（卸载依据）
用户运行 drift_check.py
  → 重新生成 dist/ 与单一源对比 → 漂移报告
```

## 7. 边界与取舍

- **不做**：loop 契约（C-\*/T-\*）、MCP App、Web UI、kb 内容（00-vision 非目标）。
- **取舍**：记忆规程不绑定特定宿主记忆 API（保持宿主无关），代价是记忆格式无法强校验（依赖宿主机制质量）。
