from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1800, 760
OUT = Path("output/project-differentiation-table.png")
OUT.parent.mkdir(exist_ok=True)

BG = (255, 255, 255, 0)
CARD = (250, 255, 248, 255)
HEADER = (214, 240, 205, 255)
SUBHEADER = (234, 249, 228, 255)
ROW_A = (255, 255, 255, 255)
ROW_B = (244, 252, 241, 255)
LINE = (91, 142, 85, 255)
TEXT = (23, 54, 31, 255)
MUTED = (62, 90, 65, 255)
GREEN = (94, 169, 77, 255)
GREEN_DARK = (48, 124, 57, 255)

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"

img = Image.new("RGBA", (W, H), BG)
d = ImageDraw.Draw(img)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


title_font = font(FONT_BOLD, 36)
head_font = font(FONT_BOLD, 26)
cell_bold = font(FONT_BOLD, 22)
cell_font = font(FONT_REG, 22)
caption_font = font(FONT_BOLD, 27)


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


def center_text(text: str, box: tuple[int, int, int, int], f: ImageFont.FreeTypeFont, fill=TEXT) -> None:
    x1, y1, x2, y2 = box
    lines = wrap_lines(text, f, x2 - x1 - 24)
    line_h = text_size("가", f)[1] + 5
    total_h = len(lines) * line_h - 5
    y = y1 + ((y2 - y1) - total_h) / 2
    for line in lines:
        tw, _ = text_size(line, f)
        d.text((x1 + ((x2 - x1) - tw) / 2, y), line, font=f, fill=fill)
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
) -> None:
    d.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=CARD, outline=LINE, width=3)
    title_h = 74
    header_h = 62
    d.rounded_rectangle((x, y, x + w, y + title_h), radius=18, fill=HEADER, outline=LINE, width=3)
    d.rectangle((x, y + title_h - 18, x + w, y + title_h), fill=HEADER)
    center_text(title, (x, y, x + w, y + title_h), title_font)

    hy = y + title_h
    d.rectangle((x, hy, x + w, hy + header_h), fill=SUBHEADER, outline=LINE, width=3)
    cx = x
    for i, col in enumerate(cols):
        cw = col_widths[i]
        if i:
            d.line((cx, hy, cx, y + h), fill=LINE, width=3)
        center_text(col, (cx, hy, cx + cw, hy + header_h), head_font)
        cx += cw

    row_h = (h - title_h - header_h) // len(rows)
    ry = hy + header_h
    for r, row in enumerate(rows):
        d.rectangle((x, ry, x + w, ry + row_h), fill=ROW_A if r % 2 == 0 else ROW_B)
        d.line((x, ry, x + w, ry), fill=LINE, width=3)
        cx = x
        for i, txt in enumerate(row):
            cw = col_widths[i]
            center_text(txt, (cx + 12, ry + 6, cx + cw - 12, ry + row_h - 6), cell_bold if i == 0 else cell_font, TEXT if i == 0 else MUTED)
            cx += cw
        ry += row_h


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

draw_table(20, 20, 780, 560, "기존 제품/서비스", ("제품", "한계점"), left_rows, (330, 450))
draw_table(1000, 20, 780, 560, "우리의 제품", ("기능", "차별성"), right_rows, (240, 540))

arrow = [(845, 275), (938, 275), (938, 227), (990, 300), (938, 373), (938, 325), (845, 325)]
d.polygon(arrow, fill=GREEN)
d.line(arrow + [arrow[0]], fill=GREEN_DARK, width=4)
center_text("통합", (840, 390, 992, 440), caption_font, GREEN_DARK)

d.rounded_rectangle((20, 620, 1780, 735), radius=18, fill=(249, 255, 247, 255), outline=LINE, width=3)
center_text(
    "Harvest to sale은 자동 수확 → DB 저장 → LLM 판매 판단 → 판매페이지까지 하나의 파이프라인으로 연결",
    (45, 640, 1755, 715),
    font(FONT_BOLD, 30),
    TEXT,
)

img.save(OUT)
print(OUT.resolve())
