#!/usr/bin/env python3
"""为每篇文章生成封面图和配图(PNG)。依赖 Pillow;需要系统里有中文字体(默认文泉驿正黑)。

用法:python3 make_images.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FONT_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/msyh.ttc",
]
NAVY, ORANGE, INK, MUTED = (20, 33, 61), (252, 163, 17), (30, 36, 50), (110, 118, 135)
LIGHT, WHITE, GREEN, RED, BLUE = (244, 246, 250), (255, 255, 255), (46, 160, 110), (214, 69, 65), (52, 104, 192)


def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise SystemExit("找不到中文字体，请在 FONT_PATHS 里加上你系统的中文字体路径")


def wrap(draw, text, fnt, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if draw.textlength(cur + ch, font=fnt) > maxw and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


def text_h(lines, size, gap=1.35):
    return int(len(lines) * size * gap)


def draw_lines(d, xy, lines, fnt, fill, size, gap=1.35):
    x, y = xy
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += int(size * gap)
    return y


def cover(folder, kicker, title, sub):
    img = Image.new("RGB", (1800, 766), NAVY)
    d = ImageDraw.Draw(img)
    d.ellipse((1250, -250, 2100, 600), fill=(31, 49, 88))
    d.ellipse((1500, 300, 2000, 800), fill=(39, 60, 105))
    d.rectangle((100, 110, 112, 656), fill=ORANGE)
    kf = font(46)
    kw = d.textlength(kicker, font=kf)
    d.rounded_rectangle((160, 100, 160 + kw + 60, 180), 40, fill=ORANGE)
    d.text((190, 112), kicker, font=kf, fill=NAVY)
    tf = font(112)
    tl = wrap(d, title, tf, 1450)
    y = draw_lines(d, (160, 230), tl, tf, WHITE, 112, 1.25)
    sf = font(50)
    draw_lines(d, (160, 566), wrap(d, sub, sf, 1450), sf, (190, 200, 220), 50)
    save(img, folder, "cover.png")


def save(img, folder, name):
    out = os.path.join(ROOT, folder, "images")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, name), optimize=True)
    print("生成", folder, name)


def cards(folder, name, title, items, accents=None, width=1080, numbered=True):
    """纵向流程卡片。items: [(标题， 说明)]"""
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    hf, bf, tf = font(40), font(32), font(46)
    pad, cw = 40, width - 80
    laid = []
    for h, b in items:
        bl = wrap(tmp, b, bf, cw - 150) if b else []
        laid.append((h, bl, 40 + 56 + text_h(bl, 32) + 30))
    total = 150 + sum(x[2] for x in laid) + 50 * (len(laid) - 1) + 60
    img = Image.new("RGB", (width, total), LIGHT)
    d = ImageDraw.Draw(img)
    d.text((pad, 48), title, font=tf, fill=INK)
    y = 150
    for i, (h, bl, ch) in enumerate(laid):
        col = (accents or [BLUE, ORANGE, GREEN, RED, NAVY, MUTED])[i % 6]
        d.rounded_rectangle((pad, y, pad + cw, y + ch), 22, fill=WHITE, outline=(222, 226, 235), width=2)
        d.rounded_rectangle((pad, y, pad + 14, y + ch), 7, fill=col)
        if numbered:
            d.ellipse((pad + 40, y + 34, pad + 100, y + 94), fill=col)
            d.text((pad + 70, y + 64), str(i + 1), font=hf, fill=WHITE, anchor="mm")
        d.text((pad + 125, y + 34), h, font=hf, fill=INK)
        draw_lines(d, (pad + 125, y + 98), bl, bf, MUTED, 32)
        y += ch
        if i < len(laid) - 1:
            d.polygon([(width // 2 - 18, y + 8), (width // 2 + 18, y + 8), (width // 2, y + 38)], fill=(190, 196, 210))
            y += 50
    save(img, folder, name)


def two_col(folder, name, title, lh, litems, rh, ritems, lcol=BLUE, rcol=ORANGE, width=1080):
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    hf, bf, tf = font(42), font(34), font(46)
    colw = (width - 120) // 2
    def lay(items):
        return [wrap(tmp, t, bf, colw - 60) for t in items]
    ll, rl = lay(litems), lay(ritems)
    def height(ls):
        return 130 + sum(text_h(l, 34) + 22 for l in ls) + 30
    h = max(height(ll), height(rl))
    img = Image.new("RGB", (width, 150 + h + 50), LIGHT)
    d = ImageDraw.Draw(img)
    d.text((40, 48), title, font=tf, fill=INK)
    for x, head, ls, col in ((40, lh, ll, lcol), (40 + colw + 40, rh, rl, rcol)):
        d.rounded_rectangle((x, 150, x + colw, 150 + h), 22, fill=WHITE, outline=(222, 226, 235), width=2)
        d.rounded_rectangle((x, 150, x + colw, 150 + 90), 22, fill=col)
        d.rectangle((x, 150 + 60, x + colw, 150 + 90), fill=col)
        d.text((x + colw // 2, 150 + 46), head, font=hf, fill=WHITE, anchor="mm")
        y = 150 + 120
        for l in ls:
            d.ellipse((x + 30, y + 14, x + 44, y + 28), fill=col)
            d.text((x + 58, y), l[0], font=bf, fill=INK)
            y2 = y + int(34 * 1.35)
            for extra in l[1:]:
                d.text((x + 58, y2), extra, font=bf, fill=INK)
                y2 += int(34 * 1.35)
            y = y2 + 22
    save(img, folder, name)


def code_card(folder, name, title, lines, width=1080):
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cf, tf = font(31), font(46)
    wrapped = []
    for ln in lines:
        wrapped += wrap(tmp, ln, cf, width - 140)
    h = 220 + text_h(wrapped, 31, 1.5) + 70
    img = Image.new("RGB", (width, h), LIGHT)
    d = ImageDraw.Draw(img)
    d.text((40, 48), title, font=tf, fill=INK)
    d.rounded_rectangle((40, 140, width - 40, h - 30), 22, fill=(28, 34, 52))
    for i, c in enumerate((RED, ORANGE, GREEN)):
        d.ellipse((72 + i * 40, 168, 94 + i * 40, 190), fill=c)
    draw_lines(d, (76, 220), wrapped, cf, (226, 232, 245), 31, 1.5)
    save(img, folder, name)


F1 = "01-你收到的审稿意见可能不是人写的"
F2 = "02-AI十分钟生成创新模块研究生的创新还值钱吗"
F3 = "03-组会听不懂用AI当你的私人学长"
F4 = "04-用脚本揪出参考文献里的幽灵论文"
F5 = "05-给AI写一份课题入职手册"
F6 = "06-论文AIGC率被误判后的五份自证材料"

if __name__ == "__main__":
    cover(F1, "投稿人必看", "你收到的审稿意见，可能根本不是人写的", "六步应对法 · 附写作自保清单")
    cards(F1, "fig1.png", "收到“疑似 AI 味”的审稿意见，这样处理", [
        ("先别下结论", "你没法证明“这是 AI 写的”,在 rebuttal 里指控只会让自己被动。"),
        ("给每条意见分类", "有实质内容 / 空泛套话 / 与事实不符，三类分开处理。"),
        ("事实错误：拿原文说话", "标出页码、图表编号、公式，语气平静，一条一条纠正。"),
        ("套话：把它变具体", "“理解审稿人关注……,我们在第 X 节新增了……”,让空话变成可检验的改进。"),
        ("严重怀疑：走正式渠道", "按会议规定向领域主席/程序主席保密反馈，附事实依据，不在公开回复里争吵。"),
        ("留好证据", "保存评审原文、你的回复和修改版本，便于之后申诉。"),
    ])
    cover(F2, "观点", "AI 十分钟生成一个“创新模块”,研究生的创新还值钱吗?", "科研两轨制：什么交给 AI,什么必须自己扛")
    two_col(F2, "fig1.png", "科研两轨制", "轨道 A：交给 AI", [
        "复现 baseline、跑通开源代码", "画图、排版、统一格式", "翻译、润色、整理文献笔记", "写样板代码和实验脚本"],
        "轨道 B：必须自己", [
        "选问题：值不值得做", "提假设：为什么会有效", "设计能“证伪”的实验", "判断结果是否可信、怎么解释"],
        lcol=BLUE, rcol=ORANGE)
    cover(F3, "研一新生", "组会听不懂?开会前 30 分钟让 AI 当你的私人学长", "三条提示词 · 直接复制就能用")
    cards(F3, "fig1.png", "组会前 30 分钟时间线", [
        ("T-30  速读：先搞懂它在干什么", "让 AI 用本科生能懂的话讲清：要解决什么问题、核心想法、和旧方法的区别。"),
        ("T-20  扫盲：术语清单", "列出 10 个你可能不懂的术语：一句话解释 + 一个类比 + 在本文里的作用。"),
        ("T-10  备问：准备一个问题", "让 AI 以初学者视角提 3 个问题，挑一个改成自己的话。"),
        ("T-0   开会：三栏笔记", "听懂的 / 没听懂的 / 要问的。散会后 24 小时内回头补课。"),
    ], accents=[BLUE, GREEN, ORANGE, NAVY])
    cover(F4, "避坑 · 附脚本", "连顶会论文都被查出假引用，你的参考文献查了吗?", "一个免费小脚本，批量揪出“幽灵论文”")
    cards(F4, "fig1.png", "参考文献验真流程", [
        ("整理参考文献", "每条一行，存成 refs.txt。"),
        ("脚本批量检索 Crossref", "按标题检索，取最接近的一条记录。"),
        ("比对标题相似度", "高：基本可信;中：人工看一眼;低/无结果：重点复核。"),
        ("人工复核“存疑”项", "到 Google Scholar、知网、arXiv 逐条确认作者、年份、期刊。"),
        ("读原文确认结论", "文献存在 ≠ 它真的支持你的论点，关键引用必须读原文。"),
    ])
    cover(F5, "AI 工具教程", "你的 AI 为什么总是不懂你的课题?", "因为你没给它写这份“入职手册”")
    code_card(F5, "fig1.png", "项目根目录放一个说明文件", [
        "我的课题/",
        "├─ CLAUDE.md      ← Claude Code 读这个",
        "├─ AGENTS.md      ← Codex 读这个(内容可以一样)",
        "├─ data/",
        "│   ├─ raw/       ← 原始数据，禁止修改",
        "│   └─ processed/",
        "├─ src/",
        "├─ results/",
        "└─ 实验日志.md",
    ])
    cover(F6, "毕业季 · 自保", "“我自己写的论文，AIGC 率却很高?”", "被误判之后，你需要这五份证据")
    cards(F6, "fig1.png", "五份自证材料", [
        ("写作版本历史", "Word / WPS 历史版本、Overleaf History、Git 提交记录。"),
        ("文献阅读痕迹", "Zotero 批注、读书笔记、带日期的摘录。"),
        ("原始数据与实验记录", "数据文件、代码、实验日志、中间结果截图。"),
        ("与导师的修改往来", "邮件或聊天记录里的修改稿与意见。"),
        ("早期提纲与草稿", "手写提纲、思路图、最初的几版粗稿。"),
    ], accents=[BLUE, GREEN, ORANGE, RED, NAVY])
