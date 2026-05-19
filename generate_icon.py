"""
Generates the ZHud icon: Z in green + Hud in white on dark background.
Creates: frontend/assets/icon.png  (512x512)
         frontend/assets/icon.ico  (multi-size: 256, 128, 64, 48, 32, 16)
"""
from PIL import Image, ImageDraw, ImageFont
import os, sys

ASSETS = os.path.join(os.path.dirname(__file__), "frontend", "assets")
os.makedirs(ASSETS, exist_ok=True)

SIZE = 512
BG   = (15, 23, 42)       # #0f172a  dark navy
GREEN = (74, 222, 128)    # #4ade80  Tailwind green-400
WHITE = (255, 255, 255)
RADIUS = 72

def make_icon(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded-corner background
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(RADIUS * size / SIZE), fill=BG)

    # Load bold font
    font_candidates = ["arialbd.ttf", "Arial Bold.ttf", "verdanab.ttf", "calibrib.ttf"]

    # Auto-size font so "ZHud" fits within 82% of icon width
    MAX_W = int(size * 0.82)
    font_size = int(size * 0.55)
    font = None

    while font_size > 20:
        f = None
        for name in font_candidates:
            try:
                f = ImageFont.truetype(name, font_size)
                break
            except Exception:
                pass
        if f is None:
            f = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), "ZHud", font=f)
        if (bbox[2] - bbox[0]) <= MAX_W:
            font = f
            break
        font_size -= 8

    if font is None:
        font = ImageFont.load_default()

    # Measure each part separately for two-colour rendering
    z_bbox   = draw.textbbox((0, 0), "Z",   font=font)
    hud_bbox = draw.textbbox((0, 0), "Hud", font=font)
    z_w   = z_bbox[2]   - z_bbox[0]
    hud_w = hud_bbox[2] - hud_bbox[0]
    total_w = z_w + hud_w
    text_h  = max(z_bbox[3] - z_bbox[1], hud_bbox[3] - hud_bbox[1])

    x_start = (size - total_w) // 2
    y_start = (size - text_h) // 2

    # Draw "Z" in green, "Hud" in white
    draw.text((x_start,       y_start), "Z",   font=font, fill=GREEN)
    draw.text((x_start + z_w, y_start), "Hud", font=font, fill=WHITE)

    return img


# ── Generate 512×512 PNG ──────────────────────────────────────────────────────
png_path = os.path.join(ASSETS, "icon.png")
img512 = make_icon(512)
img512.save(png_path, "PNG")
print(f"[ok] {png_path}")

# ── Generate multi-size ICO ───────────────────────────────────────────────────
ico_path = os.path.join(ASSETS, "icon.ico")
sizes = [256, 128, 64, 48, 32, 16]
frames = [make_icon(s) for s in sizes]
frames[0].save(
    ico_path,
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=frames[1:],
)
print(f"[ok] {ico_path}")
print("Done! Icon files created.")
