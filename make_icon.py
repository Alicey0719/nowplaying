"""Build-time script: generate _icon.ico and _icon.png for PyInstaller."""
from PIL import Image

PADDING = 0.02  # content area as fraction of final size


def make(size: int = 256) -> Image.Image:
    src = Image.open("icon_source.png").convert("RGBA")
    bbox = src.getbbox()
    src = src.crop(bbox)

    # supersample: composite at 4x then downscale for smooth edges
    render = max(size * 4, 256)
    inner = int(render * (1 - PADDING * 2))
    tmp = src.copy()
    tmp.thumbnail((inner, inner), Image.LANCZOS)
    canvas = Image.new("RGBA", (render, render), (0, 0, 0, 0))
    x = (render - tmp.width) // 2
    y = (render - tmp.height) // 2
    canvas.paste(tmp, (x, y), tmp)
    if render != size:
        canvas = canvas.resize((size, size), Image.LANCZOS)
    return canvas


if __name__ == "__main__":
    sizes = [32, 48, 64, 128, 256]
    images = [make(s) for s in sizes]
    images[0].save("_icon.ico", format="ICO", append_images=images[1:])
    make(256).save("_icon.png")
    print("Generated _icon.ico and _icon.png")
