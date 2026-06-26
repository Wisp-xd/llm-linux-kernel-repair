from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures"

W, H = 1600, 900
FONT = "Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif"
INK = "#14213D"
MUTED = "#5B6475"
BLUE = "#2563A6"
BLUE_LIGHT = "#EAF2FA"
TEAL = "#16877A"
TEAL_LIGHT = "#E7F5F2"
ORANGE = "#D97706"
ORANGE_LIGHT = "#FFF3DD"
RED = "#B83A3A"
RED_LIGHT = "#FCECEC"
GRAY = "#E5E9EF"
GRAY_LIGHT = "#F7F8FA"
WHITE = "#FFFFFF"


def header(title: str, subtitle: str) -> list[str]:
    return [
        f'<rect width="{W}" height="{H}" fill="{WHITE}"/>',
        f'<text x="70" y="72" font-family="{FONT}" font-size="38" font-weight="700" fill="{INK}">{escape(title)}</text>',
        f'<text x="70" y="112" font-family="{FONT}" font-size="20" fill="{MUTED}">{escape(subtitle)}</text>',
        '<line x1="70" y1="140" x2="1530" y2="140" stroke="#D9DEE7" stroke-width="2"/>',
    ]


def svg_start() -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs>',
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L0,6 L9,3 z" fill="#6B7280"/>',
        '</marker>',
        '</defs>',
    ]


def box(x: int, y: int, w: int, h: int, fill: str, stroke: str, title: str, lines: list[str], title_size: int = 23, body_size: int = 17) -> list[str]:
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
        f'<text x="{x + 20}" y="{y + 32}" font-family="{FONT}" font-size="{title_size}" font-weight="700" fill="{INK}">{escape(title)}</text>',
    ]
    for idx, line in enumerate(lines):
        parts.append(
            f'<text x="{x + 20}" y="{y + 60 + idx * 24}" font-family="{FONT}" font-size="{body_size}" fill="{MUTED}">{escape(line)}</text>'
        )
    return parts


def arrow(x1: int, y1: int, x2: int, y2: int) -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#6B7280" stroke-width="2.5" marker-end="url(#arrow)"/>'


def badge(x: int, y: int, w: int, text: str, fill: str, color: str) -> list[str]:
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="32" rx="8" fill="{fill}"/>',
        f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" font-family="{FONT}" font-size="15" font-weight="700" fill="{color}">{escape(text)}</text>',
    ]


def save(name: str, parts: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    content = "\n".join(svg_start() + parts + ["</svg>"])
    (OUT / name).write_text(content, encoding="utf-8")


def flow_comparison() -> None:
    p = header(
        "CrashFixer 与本项目流程对照",
        "保留根因推理与反思，缩小系统范围，并加入 Semantic Guard 与可复现工程核验",
    )
    p += [
        f'<rect x="70" y="165" width="700" height="56" rx="8" fill="{INK}"/>',
        f'<text x="420" y="202" text-anchor="middle" font-family="{FONT}" font-size="25" font-weight="700" fill="{WHITE}">CrashFixer 参考流程</text>',
        f'<rect x="830" y="165" width="700" height="56" rx="8" fill="{BLUE}"/>',
        f'<text x="1180" y="202" text-anchor="middle" font-family="{FONT}" font-size="25" font-weight="700" fill="{WHITE}">本科课程项目实现</text>',
        '<line x1="800" y1="165" x2="800" y2="820" stroke="#D9DEE7" stroke-width="2" stroke-dasharray="8 8"/>',
    ]

    left = [
        (245, BLUE_LIGHT, BLUE, "输入证据", ["crash report + source code + execution trace"]),
        (350, BLUE_LIGHT, BLUE, "Hypothesis Generation", ["生成多个根因假设与修复方向"]),
        (455, BLUE_LIGHT, BLUE, "Self-Reflection", ["比较证据、筛选最可信假设"]),
        (560, BLUE_LIGHT, BLUE, "Patch Generation", ["根据选定假设生成候选补丁"]),
        (665, TEAL_LIGHT, TEAL, "完整动态验证", ["kernel build + VM + reproducer"]),
    ]
    right = [
        (245, BLUE_LIGHT, BLUE, "真实 kBenchSyz 输入", ["crash report + source excerpt + 可选 trace"]),
        (350, BLUE_LIGHT, BLUE, "Hypothesis + Reflection", ["三阶段 Prompt 流程，可保存中间结果"]),
        (455, ORANGE_LIGHT, ORANGE, "Replace-based Patch + Semantic Guard", ["约束删除、绕过、无依据提前 return"]),
        (560, TEAL_LIGHT, TEAL, "分层工程核验", ["轻量检查 → 真实源码 → 三路局部编译"]),
        (665, GRAY_LIGHT, MUTED, "人工语义评价", ["plausible / helpful / incorrect"]),
    ]
    for y, fill, stroke, title, lines in left:
        p += box(105, y, 630, 78, fill, stroke, title, lines, 22, 16)
    for y, fill, stroke, title, lines in right:
        p += box(865, y, 630, 78, fill, stroke, title, lines, 22, 16)
    for ys in [323, 428, 533, 638]:
        p.append(arrow(420, ys, 420, ys + 22))
        p.append(arrow(1180, ys, 1180, ys + 22))

    p += badge(110, 775, 160, "论文完整系统", RED_LIGHT, RED)
    p += badge(875, 775, 150, "轻量创新点", ORANGE_LIGHT, ORANGE)
    p += badge(1040, 775, 190, "真实源码核验", TEAL_LIGHT, TEAL)
    p += badge(1245, 775, 245, "局部编译对照验证", BLUE_LIGHT, BLUE)
    p.append(
        f'<text x="800" y="855" text-anchor="middle" font-family="{FONT}" font-size="17" fill="{MUTED}">范围差异：本项目不部署大规模分布式修复平台，也不把人工评价称为真实修复成功率</text>'
    )
    save("crashfixer_project_flow_comparison.svg", p)


def group_comparison() -> None:
    p = header(
        "三组实验输入与目标差异",
        "控制模型、样本与根因推理流程，仅改变 trace 输入和 Patch Generation 约束",
    )
    p += [
        f'<text x="165" y="185" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{MUTED}">实验组</text>',
        f'<text x="545" y="185" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{MUTED}">输入证据</text>',
        f'<text x="1055" y="185" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{MUTED}">Patch 阶段</text>',
        f'<text x="1390" y="185" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{MUTED}">比较目的</text>',
    ]

    rows = [
        (220, BLUE, "A  Baseline", [("Crash report", BLUE_LIGHT, BLUE), ("Source code", BLUE_LIGHT, BLUE)], "普通 Patch Prompt", "提供基线结果", GRAY_LIGHT, MUTED),
        (430, TEAL, "B  With Trace", [("Crash report", BLUE_LIGHT, BLUE), ("Source code", BLUE_LIGHT, BLUE), ("Trace summary", TEAL_LIGHT, TEAL)], "普通 Patch Prompt", "观察 trace 影响", TEAL_LIGHT, TEAL),
        (640, ORANGE, "C  Improved", [("Crash report", BLUE_LIGHT, BLUE), ("Source code", BLUE_LIGHT, BLUE), ("Trace summary", TEAL_LIGHT, TEAL)], "Semantic Guard Prompt", "减少截肢式修复", ORANGE_LIGHT, ORANGE),
    ]
    for y, color, label, chips, patch_text, goal, goal_fill, goal_stroke in rows:
        p.append(f'<rect x="70" y="{y}" width="1460" height="155" rx="8" fill="{WHITE}" stroke="{GRAY}" stroke-width="2"/>')
        p.append(f'<rect x="70" y="{y}" width="190" height="155" rx="8" fill="{color}"/>')
        p.append(f'<text x="165" y="{y + 88}" text-anchor="middle" font-family="{FONT}" font-size="23" font-weight="700" fill="{WHITE}">{escape(label)}</text>')
        chip_x = 305
        for text_value, fill, stroke in chips:
            width = 150 if text_value != "Trace summary" else 170
            p.append(f'<rect x="{chip_x}" y="{y + 57}" width="{width}" height="48" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            p.append(f'<text x="{chip_x + width / 2}" y="{y + 88}" text-anchor="middle" font-family="{FONT}" font-size="17" font-weight="700" fill="{stroke}">{escape(text_value)}</text>')
            chip_x += width + 18
        p.append(arrow(865, y + 81, 925, y + 81))
        patch_fill = ORANGE_LIGHT if "Semantic" in patch_text else GRAY_LIGHT
        patch_stroke = ORANGE if "Semantic" in patch_text else MUTED
        p.append(f'<rect x="945" y="{y + 42}" width="260" height="78" rx="8" fill="{patch_fill}" stroke="{patch_stroke}" stroke-width="2"/>')
        p.append(f'<text x="1075" y="{y + 88}" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{patch_stroke}">{escape(patch_text)}</text>')
        p.append(arrow(1225, y + 81, 1270, y + 81))
        p.append(f'<rect x="1290" y="{y + 42}" width="200" height="78" rx="8" fill="{goal_fill}" stroke="{goal_stroke}" stroke-width="2"/>')
        p.append(f'<text x="1390" y="{y + 88}" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{goal_stroke}">{escape(goal)}</text>')

    p += badge(70, 825, 260, "控制变量：相同 8 个 bug", BLUE_LIGHT, BLUE)
    p += badge(350, 825, 285, "相同模型与 temperature", GRAY_LIGHT, MUTED)
    p += badge(655, 825, 260, "相同 Hypothesis 流程", BLUE_LIGHT, BLUE)
    p += badge(935, 825, 240, "相同 Reflection 流程", TEAL_LIGHT, TEAL)
    p += badge(1195, 825, 335, "差异仅在 trace / Semantic Guard", ORANGE_LIGHT, ORANGE)
    save("experiment_group_input_comparison.svg", p)


def evidence_chain() -> None:
    p = header(
        "从 LLM 输出到真实源码核验的证据链",
        "逐层提高证据强度：格式可读 → 源码可应用 → 可编译 → 与 Developer Patch 对照",
    )
    stages = [
        (55, BLUE_LIGHT, BLUE, "1  LLM 输出", ["24 组 JSON", "三阶段结果留档"]),
        (270, GRAY_LIGHT, MUTED, "2  轻量检查", ["JSON 解析 24/24", "original 匹配 18/24"]),
        (485, BLUE_LIGHT, BLUE, "3  真实版本定位", ["8 个 parent commit", "Developer 8/8 可应用"]),
        (700, TEAL_LIGHT, TEAL, "4  源码适用性", ["git apply / diff", "Improved 5/8 pass"]),
        (915, TEAL_LIGHT, TEAL, "5  局部编译", ["defconfig pass", "fs/namespace.o pass"]),
        (1130, ORANGE_LIGHT, ORANGE, "6  三路对照", ["Parent / Developer / LLM", "Developer = LLM 哈希"]),
        (1345, GRAY_LIGHT, MUTED, "7  人工语义评价", ["Plausible 2", "Helpful 7 / Incorrect 15"]),
    ]
    for x, fill, stroke, title, lines in stages:
        p += box(x, 240, 195, 145, fill, stroke, title, lines, 18, 15)
    for x in [250, 465, 680, 895, 1110, 1325]:
        p.append(arrow(x, 312, x + 18, 312))

    p.append(f'<text x="70" y="455" font-family="{FONT}" font-size="24" font-weight="700" fill="{INK}">证据层级与可回答的问题</text>')
    layers = [
        (70, 490, 350, BLUE_LIGHT, BLUE, "格式层", "模型输出能否解析、检查与归档？"),
        (440, 490, 350, TEAL_LIGHT, TEAL, "源码层", "补丁能否落到真实 Linux commit？"),
        (810, 490, 350, ORANGE_LIGHT, ORANGE, "构建层", "补丁能否通过真实目标文件编译？"),
        (1180, 490, 350, GRAY_LIGHT, MUTED, "语义层", "是否接近 Developer Patch 的修复逻辑？"),
    ]
    for x, y, w, fill, stroke, title, question in layers:
        p += box(x, y, w, 110, fill, stroke, title, [question], 21, 15)

    p.append(f'<rect x="70" y="650" width="960" height="145" rx="8" fill="{TEAL_LIGHT}" stroke="{TEAL}" stroke-width="2"/>')
    p.append(f'<text x="95" y="688" font-family="{FONT}" font-size="22" font-weight="700" fill="{TEAL}">当前最强工程证据：bug_008 三路局部编译对照</text>')
    p.append(f'<text x="95" y="727" font-family="{FONT}" font-size="17" fill="{INK}">Parent 对象哈希不同；Developer Patch 与 LLM Improved Patch 的源码 diff 和目标对象 SHA-256 完全一致。</text>')
    p.append(f'<text x="95" y="762" font-family="{FONT}" font-size="16" fill="{MUTED}">说明 LLM 补丁在该目标上具备编译产物等价性，但不能替代运行时复现。</text>')

    p.append(f'<rect x="1060" y="650" width="470" height="145" rx="8" fill="{RED_LIGHT}" stroke="{RED}" stroke-width="2"/>')
    p.append(f'<text x="1085" y="688" font-family="{FONT}" font-size="22" font-weight="700" fill="{RED}">尚未完成的最高证据层</text>')
    p.append(f'<text x="1085" y="727" font-family="{FONT}" font-size="17" fill="{INK}">QEMU / syzkaller reproducer 动态验证</text>')
    p.append(f'<text x="1085" y="762" font-family="{FONT}" font-size="16" fill="{MUTED}">因此不将 plausible+helpful 称为真实修复成功率。</text>')

    p.append(
        f'<text x="800" y="855" text-anchor="middle" font-family="{FONT}" font-size="17" fill="{MUTED}">证据原则：每一层只回答自身能够支持的问题，不用静态或编译证据替代动态修复结论</text>'
    )
    save("llm_to_kernel_evidence_chain.svg", p)


def main() -> None:
    flow_comparison()
    group_comparison()
    evidence_chain()
    for path in sorted(OUT.glob("*.svg")):
        if path.name in {
            "crashfixer_project_flow_comparison.svg",
            "experiment_group_input_comparison.svg",
            "llm_to_kernel_evidence_chain.svg",
        }:
            print(path)


if __name__ == "__main__":
    main()
