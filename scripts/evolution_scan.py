#!/usr/bin/env python3
"""进化扫描器 —— 从每日日志提取模式，生成进化提案。

设计目标：
  扫描 .workbuddy/memory/YYYY-MM-DD.md 每日日志 →
  提取重复模式（L2 候选规则 / L3 规则精化 / L4 结构性提案 / 退休候选）→
  输出 Markdown 提案报告 → 供人工审批后执行。

使用：
  python scripts/evolution_scan.py [--since 2026-07-01] [--output <path>]
  不指定 --output 时，自动写入 proposals/evolution-scan-<当天日期>.md
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


# ── 关键词信号（帮助定位日志中的教训/修复/发现）─────────────────────────
SIGNAL_KEYWORDS = [
    "修复", "更正", "修正", "Bug", "bug", "漏洞", "缺口",
    "根因", "设计失误", "误判", "口误", "drift", "漂移",
    "硬编码原因", "为什么", "关键发现", "教训", "绕过",
    "失败", "错误", "不一致", "缺陷", "风险",
]

# ── 模式归类标签（从关键词到模式类型）──────────────────────────────────
# 每个类别是一组 AND 条件：(必须子串列表, 辅助子串列表)
# 必须子串：至少 1 个命中 + 辅助子串：至少 1 个命中 → 匹配
PATTERN_CATEGORIES = {
    "skill drift（双工具 skill 不对称）": (
        ["drift", "不对称", "skill 不对称", "两套"],
        ["skill", "claude", "codebuddy", "双写", "同步", "命名空间"],
    ),
    "gate bypass（闸门被绕过）": (
        ["绕过", "软闸门", "绕过去", "没拦住", "无人拦截"],
        ["G0", "闸门", "gate", "审批", "approved", "draft", "门禁"],
    ),
    "doc inconsistency（文档不一致）": (
        ["不一致", "交叉一致", "对称差", "drift", "漂移"],
        ["doc", "文档", "consistency", "00", "01", "vision", "requirements"],
    ),
    "manual override（AI 擅改未经审批）": (
        ["未重评审", "没通知", "绕审批", "擅改", "自标", "自己修改", "自己改了"],
        ["文档", "docs", "approve", "审批", "review"],
    ),
    "process gap（流程缺口）": (
        ["缺门禁", "无兜底", "没跑过", "没执行过", "没触发"],
        ["命令", "脚本", "闸门", "检查", "doc_consistency", "ddd_gate", "前置"],
    ),
}


def extract_sections(log_text: str, date_str: str) -> list[dict]:
    """从日志文本提取章节（以 ## 开头的段落）。"""
    sections = []
    current_title = None
    current_lines = []

    for line in log_text.split("\n"):
        if line.startswith("## "):
            if current_title:
                sections.append({
                    "date": date_str,
                    "title": current_title,
                    "body": "\n".join(current_lines).strip(),
                })
            current_title = line[3:].strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections.append({
            "date": date_str,
            "title": current_title,
            "body": "\n".join(current_lines).strip(),
        })

    return sections


def detect_patterns(sections: list[dict]) -> dict[str, list[dict]]:
    """对章节进行模式归类。使用 AND 条件：必须子串至少 1 个 + 辅助子串至少 1 个 → 匹配。"""
    patterns = defaultdict(list)

    for sec in sections:
        # 只看正文，不靠标题
        body = sec["body"].lower()
        if len(body) < 50:
            continue

        for category, (required_keywords, helper_keywords) in PATTERN_CATEGORIES.items():
            has_required = any(kw.lower() in body for kw in required_keywords)
            has_helper = any(kw.lower() in body for kw in helper_keywords)
            if has_required and has_helper:
                patterns[category].append(sec)

    return dict(patterns)


def extract_rules_from_claude(claude_path: str) -> set[str]:
    """从 CLAUDE.md 提取已有规则的关键句。"""
    if not os.path.exists(claude_path):
        return set()

    rules = set()
    with open(claude_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取 ## 1. ~ ## 7. 的每一条 `- ` 开头规则
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- ") and len(line) > 10:
            # 去掉前导 `- ` 和可能的 ** 加粗标记
            clean = line[2:].replace("**", "").strip()
            if len(clean) > 15:
                rules.add(clean[:80])  # 截前 80 字符做指纹

    return rules


def should_propose_rule(
    category: str, sections: list[dict], existing_rules: set[str]
) -> tuple[bool, str, str]:
    """判断是否应生成规则提案。返回 (应提案, 风险等级, 原因)。"""
    n = len(sections)
    dates = sorted(set(s["date"] for s in sections))

    # 判断是否已被现有规则覆盖
    category_keywords = category  # 类别名本身即描述
    covered = any(
        any(kw.lower() in rule.lower() for kw in category_keywords.split())
        for rule in existing_rules
    )

    if covered:
        return False, "low", f"已有规则覆盖（{category}）"

    if n >= 3:
        return True, "high", f"出现 {n} 次（{', '.join(dates)}），无规则覆盖 → L4 候选结构性提案"
    elif n >= 2:
        return True, "medium", f"出现 {n} 次（{', '.join(dates)}），无规则覆盖 → L2 候选规则"
    elif n == 1 and any(
        "绕过" in s["title"] or "漏洞" in s["title"] or "Bug" in s["title"]
        for s in sections
    ):
        return True, "low", "单次但影响大（绕过/漏洞/Bug），建议记录为低优先级候选"

    return False, "", ""


def generate_proposal(
    category: str, sections: list[dict], severity: str, reason: str
) -> str:
    """生成单条进化提案的 Markdown 文本。"""
    dates = sorted(set(s["date"] for s in sections))
    titles = [s["title"] for s in sections]

    return f"""### 进化提案：{category}

- **触发日志**：{', '.join(f'{d} §{t[:30]}' for d, t in zip(dates, titles))}
- **出现次数**：{len(sections)}
- **风险等级**：{severity}
- **判定**：{reason}
- **建议动作**：
  - {"L4：结构性提案——需新建工具/契约/脚本" if severity == "high" else "L2：规则新增——写入 CLAUDE.md 或 MEMORY.md"}
- **待审批**：用户确认后执行
"""


def find_retirement_candidates(
    claude_path: str, memory_log_dir: str, min_age_days: int = 30
) -> list[str]:
    """找退休候选——30 天以上未被日志引用的显式规则。"""
    if not os.path.exists(claude_path):
        return []

    with open(claude_path, "r", encoding="utf-8") as f:
        rules_text = f.read()

    # 收集最近 min_age_days 天日志中出现的关键词
    cutoff = (datetime.now() - timedelta(days=min_age_days)).strftime("%Y-%m-%d")
    recent_keywords = set()

    log_dir = Path(memory_log_dir)
    for log_file in sorted(log_dir.glob("????-??-??.md")):
        if log_file.stem < cutoff:
            continue
        text = log_file.read_text(encoding="utf-8")
        # 提取所有英文关键字（2+ 字母组成，来自 CLAUDE.md 的规则片段）
        words = re.findall(r"[a-zA-Z_]{4,}", text)
        recent_keywords.update(w.lower() for w in words)

    # 检查 CLAUDE.md 中每条规则的"关键词"是否在最近日志中出现过
    candidates = []
    rules = [l.strip() for l in rules_text.split("\n") if l.strip().startswith("- ")]
    for rule in rules:
        clean = rule[2:].replace("**", "").strip()
        if len(clean) < 10:
            continue
        # 提取规则中的独特关键词
        rule_kw = set(
            w.lower() for w in re.findall(r"[a-zA-Z_]{4,}", clean)
        )
        if not rule_kw:
            continue

        # 如果规则的关键词集与最近日志的关键词集完全不重叠 → 候选退休
        if not rule_kw & recent_keywords:
            # 排除基础规则（DDD 闸门本身不算退休候选）
            if any(basic in clean for basic in ["DDD", "MUST", "事实链", "铁律"]):
                continue
            candidates.append(clean[:100])

    return candidates


def main():
    parser = argparse.ArgumentParser(
        description="进化扫描器 —— 从日志提取模式，生成进化提案"
    )
    parser.add_argument(
        "--since",
        default="2026-07-01",
        help="扫描起始日期 (YYYY-MM-DD)，默认 2026-07-01",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出提案文件路径；不指定时自动写入 proposals/evolution-scan-<当天日期>.md",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="项目根目录，默认自动检测（向上找 CLAUDE.md 所在目录）",
    )
    parser.add_argument(
        "--memory-dir",
        default=None,
        help="日志目录（.workbuddy/memory/），默认从项目根向上查找 workspace 根",
    )
    args = parser.parse_args()

    # 自动检测项目根
    if args.project_root:
        root = Path(args.project_root)
    else:
        root = Path.cwd().resolve()
        while root != root.parent:
            if (root / "CLAUDE.md").exists() or (root / "CODEBUDDY.md").exists():
                break
            root = root.parent

    claude_path = root / "CLAUDE.md"

    # 日志目录：从项目根向上找 workspace 级别的 .workbuddy/memory/
    if args.memory_dir:
        memory_dir = Path(args.memory_dir)
    else:
        memory_dir = root / ".workbuddy" / "memory"
        if not memory_dir.exists():
            # 向上查——项目可能是 workspace 子项目，日志在 workspace 根
            probe = root.parent
            while probe != probe.parent:
                candidate = probe / ".workbuddy" / "memory"
                if candidate.exists():
                    memory_dir = candidate
                    break
                probe = probe.parent

    if not memory_dir.exists():
        print(f"[ERROR] 日志目录不存在：{memory_dir}", file=sys.stderr)
        print("  提示：请指定 --memory-dir 或用 --project-root 指向 workspace 根", file=sys.stderr)
        sys.exit(2)

    # ── Step 1：读取日志 ──
    all_sections = []
    log_files = sorted(memory_dir.glob("????-??-??.md"))
    log_files = [f for f in log_files if f.stem >= args.since]

    if not log_files:
        print(f"[INFO] {args.since} 之后无日志文件", file=sys.stderr)
        sys.exit(0)

    for log_file in log_files:
        try:
            text = log_file.read_text(encoding="utf-8")
        except Exception:
            continue
        date_str = log_file.stem
        sections = extract_sections(text, date_str)
        all_sections.extend(sections)

    # ── Step 2：模式检测 ──
    patterns = detect_patterns(all_sections)
    existing_rules = extract_rules_from_claude(str(claude_path))

    # ── Step 3：生成提案 ──
    proposals = []
    for category, sections in sorted(patterns.items()):
        should, severity, reason = should_propose_rule(
            category, sections, existing_rules
        )
        if should:
            proposals.append((severity, category, sections, reason))

    # 按风险排序：high > medium > low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    proposals.sort(key=lambda x: severity_order.get(x[0], 99))

    # ── Step 4：退休候选 ──
    retirement = find_retirement_candidates(str(claude_path), str(memory_dir))

    # ── Step 5：输出 ──
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# 进化扫描报告 — {today}")
    lines.append("")
    lines.append(f"扫描范围：{args.since} ~ {today}（{len(log_files)} 个日志文件）")
    lines.append(f"提取章节：{len(all_sections)} 个")
    lines.append(f"识别模式：{len(patterns)} 类")
    lines.append("")

    if proposals:
        lines.append(f"## 进化提案（{len(proposals)} 条）")
        lines.append("")
        for severity, category, sections, reason in proposals:
            lines.append(
                generate_proposal(category, sections, severity, reason)
            )
    else:
        lines.append("## 进化提案")
        lines.append("")
        lines.append("无待处理提案。当前日志中所有模式已沉淀为规则。")

    if retirement:
        lines.append(f"## 退休候选（{len(retirement)} 条）")
        lines.append("")
        lines.append("以下规则在最近 30 天日志中未被引用：")
        lines.append("")
        for i, rule in enumerate(retirement, 1):
            lines.append(f"{i}. `{rule}`")
        lines.append("")
        lines.append("> ⚠️ 仅作候选——请人工确认这些规则是否真的已不再需要。")
    else:
        lines.append("")
        lines.append("## 退休候选")
        lines.append("")
        lines.append("无退休候选。所有规则在最近 30 天内均有触发或属于基础铁律。")

    lines.append("")
    lines.append("---")
    lines.append(f"*扫描完成于 {datetime.now().isoformat()}*")

    output_text = "\n".join(lines)

    if args.output:
        output_path = Path(args.output)
    else:
        # 默认自动写入 proposals/evolution-scan-<当天日期>.md，与内容标题日期保持一致
        output_path = Path("proposals") / f"evolution-scan-{today}.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"[OK] 提案已写入 {output_path}", file=sys.stderr)

    print(output_text)


if __name__ == "__main__":
    main()
