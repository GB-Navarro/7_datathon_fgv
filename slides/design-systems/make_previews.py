"""Compose contact sheets from the browser screenshots; no charts are redrawn."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PREVIEWS = HERE / "previews"
FONT = HERE / "assets/fonts/Manrope.ttf"
heading = ImageFont.truetype(str(FONT), 19)
label = ImageFont.truetype(str(FONT), 15)
names = {
    "aureo": "01 / ÁUREO — Lastro & evidência",
    "vertice": "02 / VÉRTICE — Mercado & medida",
    "meridiano": "03 / MERIDIANO — Tempo & acesso",
}

for theme, title in names.items():
    board = Image.new("RGB", (1336, 1640), "#0B100E")
    draw = ImageDraw.Draw(board)
    draw.text((20, 18), title, font=heading, fill="#D8BC7A")
    for i in range(8):
        x, y = 20 + (i % 2) * 658, 62 + (i // 2) * 390
        with Image.open(PREVIEWS / f"{theme}-{i+1:02d}.png") as original:
            thumb = original.convert("RGB")
        thumb.thumbnail((638, 359), Image.Resampling.LANCZOS)
        board.paste(thumb, (x, y))
        draw.text((x, y + 366), f"{i+1:02d} / 08", font=label, fill="#BAC1B8")
    board.save(PREVIEWS / f"{theme}-prancha.png")

board = Image.new("RGB", (1848, 1164), "#0B100E")
draw = ImageDraw.Draw(board)
draw.text((24, 20), "BITFLOW / TRÊS DIREÇÕES VISUAIS", font=heading, fill="#D8BC7A")
for j, (theme, title) in enumerate(names.items()):
    x = 24 + j * 608
    draw.text((x, 65), title, font=label, fill="#E8E5DB")
    for k, number in enumerate([1, 2, 5]):
        with Image.open(PREVIEWS / f"{theme}-{number:02d}.png") as original:
            thumb = original.convert("RGB")
        thumb.thumbnail((584, 329), Image.Resampling.LANCZOS)
        board.paste(thumb, (x, 98 + k * 351))
board.save(PREVIEWS / "comparativo.png")
print("Pranchas e comparativo atualizados.")
