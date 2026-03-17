from pathlib import Path

from PIL import Image, ImageDraw

from pxl.utils import hex_to_rgb


def save_png(
    pixels: list[list[str]],
    output_path: str | Path,
    scale: int = 16,
) -> None:
    """Save a pixel grid as a PNG file.

    Args:
        pixels: List of rows, each a list of hex color strings.
        output_path: Destination file path.
        scale: Physical pixels per grid cell (default 16).
               16x16 grid at scale=16 → 256×256 PNG.
    """
    height = len(pixels)
    width = len(pixels[0]) if pixels else 0

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (width * scale, height * scale))
    draw = ImageDraw.Draw(img)

    for row_idx, row in enumerate(pixels):
        for col_idx, hex_color in enumerate(row):
            r, g, b = hex_to_rgb(hex_color)
            # #000000 is treated as transparent background
            alpha = 0 if hex_color.upper() == "#000000" else 255
            color = (r, g, b, alpha)
            x0 = col_idx * scale
            y0 = row_idx * scale
            draw.rectangle([(x0, y0), (x0 + scale - 1, y0 + scale - 1)], fill=color)

    img.save(str(output_path), "PNG")
