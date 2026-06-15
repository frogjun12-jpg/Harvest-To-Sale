from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1920, 1080
OUT = Path("output/project-differentiation-slide-v2.png")
OUT.parent.mkdir(exist_ok=True)

BG = (242, 249, 240)
PANEL = (252, 255, 250)
PANEL_ALT = (239, 249, 237)
OUR_PANEL = (248, 255, 246)
LINE = (91, 142, 85)
WHITE = (24, 53, 31)
MUTED = (64, 91, 67)
GREEN = (92, 171, 77)
GREEN2 = (52, 128, 61)
GOLD = (40, 123, 54)
RED = (211, 69, 52)

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"
FONT_SERIF = "C:/Windows/Fonts/georgia.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# Background orchard silhouettes.
for x in range(-80, W + 100, 170):
    base = 850 + ((x // 170) % 2) * 22
    d.rectangle((x + 66, base - 30, x + 88, H), fill=(132, 104, 67))
    d.ellipse((x, base - 145, x + 150, base + 10), fill=(190, 224, 173))
    d.ellipse((x + 35, base - 182, x + 175, base - 20), fill=(177, 217, 160))
    d.ellipse((x - 30, base - 105, x + 110, base + 40), fill=(202, 232, 188))
    for ax, ay in [(x + 42, base - 80), (x + 91, base - 128), (x + 124, base - 62)]:
        d.ellipse((ax, ay, ax + 16, ay + 16), fill=(116, 37, 31))

# Subtle tech grid.
for i in range(12):
    d.line((980, 120 + i * 70, 1880, 210 + i * 70), fill=(197, 224, 190), width=2)
for i in range(9):
    x = 1030 + i * 92
    y = 160 + (i % 4) * 95
    d.ellipse((x, y, x + 9, y + 9), fill=(104, 166, 96))

title_project = font(FONT_SERIF if Path(FONT_SERIF).exists() else FONT_BOLD, 66)
title_ko = font(FONT_BOLD, 72)
sub_font = font(FONT_BOLD, 29)
h_font = font(FONT_BOLD, 33)
cell_font = font(FONT_BOLD, 25)
small_font = font(FONT_REG, 22)
small_bold = font(FONT_BOLD, 22)
foot_font = font(FONT_BOLD, 29)
note_font = font(FONT_REG, 18)


def text_size(text: str, f: ImageFont.FreeTypeFont) -> tuple[int, int]:
    b = d.textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1]


def wrap_lines(text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for part in str(text).split("\n"):
        cur = ""
        for ch in part:
            test = cur + ch
            if text_size(test, f)[0] <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines


def center_text(
    text: str,
    box: tuple[int, int, int, int],
    f: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int] = WHITE,
    spacing: int = 5,
) -> None:
    x1, y1, x2, y2 = box
    lines = wrap_lines(text, f, x2 - x1 - 24)
    line_h = text_size("가", f)[1] + spacing
    total_h = len(lines) * line_h - spacing
    y = y1 + ((y2 - y1) - total_h) / 2
    for line in lines:
        tw, _ = text_size(line, f)
        d.text((x1 + ((x2 - x1) - tw) / 2, y), line, font=f, fill=fill)
        y += line_h


def left_text(
    text: str,
    box: tuple[int, int, int, int],
    f: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int] = WHITE,
    spacing: int = 5,
) -> None:
    x1, y1, x2, y2 = box
    lines = wrap_lines(text, f, x2 - x1)
    line_h = text_size("가", f)[1] + spacing
    total_h = len(lines) * line_h - spacing
    y = y1 + ((y2 - y1) - total_h) / 2
    for line in lines:
        d.text((x1, y), line, font=f, fill=fill)
        y += line_h


def draw_table(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    cols: tuple[str, str],
    rows: list[tuple[str, str]],
    col_widths: tuple[int, int],
    accent: bool = False,
) -> None:
    d.rounded_rectangle((x + 10, y + 12, x + w + 10, y + h + 12), radius=14, fill=(198, 218, 194))
    d.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=14,
        fill=OUR_PANEL if accent else PANEL,
        outline=LINE,
        width=3,
    )
    title_h = 78
    header_h = 68
    title_fill = (208, 239, 199) if accent else (220, 241, 213)
    d.rounded_rectangle((x, y, x + w, y + title_h), radius=14, fill=title_fill, outline=LINE, width=3)
    d.rectangle((x, y + title_h - 14, x + w, y + title_h), fill=title_fill)
    center_text(title, (x, y, x + w, y + title_h), h_font)

    hy = y + title_h
    d.rectangle((x, hy, x + w, hy + header_h), fill=(232, 247, 227), outline=LINE, width=3)
    cx = x
    for i, col in enumerate(cols):
        cw = col_widths[i]
        if i:
            d.line((cx, hy, cx, y + h), fill=LINE, width=3)
        center_text(col, (cx, hy, cx + cw, hy + header_h), cell_font)
        cx += cw

    row_h = (h - title_h - header_h) // len(rows)
    ry = hy + header_h
    for r, row in enumerate(rows):
        d.rectangle((x, ry, x + w, ry + row_h), fill=PANEL_ALT if r % 2 else PANEL)
        d.line((x, ry, x + w, ry), fill=LINE, width=3)
        cx = x
        for i, txt in enumerate(row):
            cw = col_widths[i]
            f = small_bold if i == 0 else small_font
            fill = WHITE if i == 0 else MUTED
            center_text(txt, (cx + 10, ry + 5, cx + cw - 10, ry + row_h - 5), f, fill)
            cx += cw
        ry += row_h


d.text((62, 42), "PROJECT", font=title_project, fill=WHITE)
d.text((380, 38), "차별성", font=title_ko, fill=WHITE)
d.rounded_rectangle((70, 123, 342, 166), radius=22, fill=(219, 244, 211), outline=(104, 161, 94), width=2)
center_text("수확부터 판매까지", (70, 123, 342, 166), sub_font)

left_rows = [
    ("Abundant Robotics\n사과 수확 로봇", "사과 picking 중심\n판매·주문 연동 없음"),
    ("Tevel Aerobotics\n과일 수확 로봇", "공중 로봇 기반 수확\n판매 전략 연동 없음"),
    ("FFRobotics\n과일 수확 로봇", "수확 자동화 중심\n판매 의사결정 X"),
    ("AGRIVI\n농장 관리 SW", "관리·분석 중심\n로봇 수확/판매 자동화 X"),
]
right_rows = [
    ("자동 수확", "터틀봇이 수확 결과를\nFastAPI로 전송"),
    ("통합 DB", "수확·재고·주문·RAG 문서를\nMariaDB 기반으로 관리"),
    ("LLM 판단", "시세·뉴스·재고를 종합해\n판매 전략 답변"),
    ("판매 연결", "상품 등록·판매페이지·주문 확인까지\n하나의 흐름으로 통합"),
]

draw_table(62, 192, 820, 570, "기존 제품/서비스", ("제품", "한계점"), left_rows, (355, 465), False)
draw_table(1080, 192, 780, 570, "우리의 제품", ("기능", "차별성"), right_rows, (245, 535), True)

arrow = [(915, 455), (1000, 455), (1000, 405), (1070, 477), (1000, 549), (1000, 499), (915, 499)]
d.polygon(arrow, fill=GREEN)
d.line(arrow + [arrow[0]], fill=GREEN2, width=4)
center_text("통합", (925, 565, 1065, 610), font(FONT_BOLD, 36), GOLD)

d.rounded_rectangle((60, 812, 1860, 975), radius=20, fill=(249, 255, 247), outline=(119, 173, 108), width=2)
center_text("기존 제품은 수확·선별·관리·분석 기능이 각각 분리되어 있음", (90, 827, 1830, 875), foot_font, MUTED)
center_text(
    "Harvest to sale은 자동 수확 → DB 저장 → LLM 판매 판단 → 판매페이지까지 하나의 파이프라인으로 연결",
    (90, 887, 1830, 955),
    font(FONT_BOLD, 31),
    WHITE,
)

left_text(
    "사례 기준: Abundant Robotics, Tevel Aerobotics, FFRobotics, AGRIVI",
    (64, 1000, 900, 1030),
    note_font,
    (170, 190, 168),
)

for ax, ay in [(1702, 54), (1754, 84), (1810, 58)]:
    d.ellipse((ax, ay, ax + 34, ay + 34), fill=RED)
    d.line((ax + 17, ay + 1, ax + 22, ay - 13), fill=(95, 60, 32), width=4)
    d.ellipse((ax + 23, ay - 13, ax + 43, ay - 2), fill=(71, 143, 61))

img.save(OUT)
print(OUT.resolve())
