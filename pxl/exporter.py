import math
from pathlib import Path

from PIL import Image, ImageDraw

from pxl.utils import hex_to_rgb


def _pixels_to_image(pixels: list[list[str]], scale: int) -> Image.Image:
    """Render a pixel grid to a Pillow RGBA image."""
    height = len(pixels)
    width = len(pixels[0]) if pixels else 0
    img = Image.new("RGBA", (width * scale, height * scale))
    draw = ImageDraw.Draw(img)
    for row_idx, row in enumerate(pixels):
        for col_idx, hex_color in enumerate(row):
            r, g, b = hex_to_rgb(hex_color)
            alpha = 0 if hex_color.upper() == "#000000" else 255
            x0 = col_idx * scale
            y0 = row_idx * scale
            draw.rectangle([(x0, y0), (x0 + scale - 1, y0 + scale - 1)], fill=(r, g, b, alpha))
    return img


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
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    _pixels_to_image(pixels, scale).save(str(output_path), "PNG")


def save_gif(
    frames: list[list[list[str]]],
    output_path: str | Path,
    scale: int = 16,
    fps: int = 8,
) -> None:
    """Save a list of pixel grids as an animated GIF."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    duration_ms = max(20, 1000 // fps)
    imgs = [
        _pixels_to_image(f, scale).quantize(colors=255, dither=Image.Dither.NONE)
        for f in frames
    ]
    imgs[0].save(
        str(output_path),
        format="GIF",
        save_all=True,
        append_images=imgs[1:],
        duration=duration_ms,
        loop=0,
        transparency=0,
        disposal=2,
    )


def save_apng(
    frames: list[list[list[str]]],
    output_path: str | Path,
    scale: int = 16,
    fps: int = 8,
) -> None:
    """Save a list of pixel grids as an animated PNG (APNG)."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    duration_ms = max(20, 1000 // fps)
    imgs = [_pixels_to_image(f, scale) for f in frames]
    imgs[0].save(
        str(output_path),
        format="PNG",
        save_all=True,
        append_images=imgs[1:],
        duration=duration_ms,
        loop=0,
    )


def save_sprite_sheet(
    frames: list[list[list[str]]],
    output_path: str | Path,
    scale: int = 16,
    columns: int | None = None,
) -> None:
    """Save a list of pixel grids as a sprite sheet PNG.

    Args:
        frames: List of pixel grids (each a list of rows of hex strings).
        output_path: Destination file path.
        scale: Physical pixels per grid cell.
        columns: How many frames per row (default: all frames in one row).
    """
    n = len(frames)
    cols = min(columns, n) if columns else n
    rows = math.ceil(n / cols)

    frame_w = len(frames[0][0]) * scale if frames else 0
    frame_h = len(frames[0]) * scale if frames else 0

    sheet = Image.new("RGBA", (cols * frame_w, rows * frame_h))
    for idx, frame in enumerate(frames):
        row, col = divmod(idx, cols)
        sheet.paste(_pixels_to_image(frame, scale), (col * frame_w, row * frame_h))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(str(output_path), "PNG")
