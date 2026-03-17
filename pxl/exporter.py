from pathlib import Path

from PIL import Image

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

    img = Image.new("RGBA", (width * scale, height * scale))

    for row_idx, row in enumerate(pixels):
        for col_idx, hex_color in enumerate(row):
            r, g, b = hex_to_rgb(hex_color)
            # #000000 is treated as transparent background
            alpha = 0 if hex_color.upper() == "#000000" else 255
            color = (r, g, b, alpha)
            x0 = col_idx * scale
            y0 = row_idx * scale
            for dy in range(scale):
                for dx in range(scale):
                    img.putpixel((x0 + dx, y0 + dy), color)

    img.save(str(output_path), "PNG")
