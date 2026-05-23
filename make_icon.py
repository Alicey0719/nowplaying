"""Build-time script: generate _icon.ico for PyInstaller."""
from PIL import Image, ImageDraw

ACCENT = "#cba6f7"
BG     = "#1e1e2e"


def make(size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=ACCENT)
    s = size // 8
    x = size * 17 // 32
    d.rectangle([x, s * 2, x + s, s * 5], fill=BG)
    d.polygon([(x + s, s * 2), (x + s * 4, s * 3), (x + s, s * 4)], fill=BG)
    cx, cy, r = size * 13 // 32, s * 5, s + 1
    d.ellipse([cx - r, cy - r + 2, cx + r, cy + r + 2], fill=BG)
    return img


if __name__ == "__main__":
    base = make(256)
    sizes = [16, 32, 48, 64, 128, 256]
    images = [base.resize((s, s), Image.LANCZOS) for s in sizes]
    images[0].save("_icon.ico", format="ICO", append_images=images[1:])
    print("Generated _icon.ico")
