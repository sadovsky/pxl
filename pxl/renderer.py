from pxl.utils import hex_to_rgb

RESET = "\033[0m"


def print_preview(pixels: list[list[str]]) -> None:
    """Render pixel art to terminal using ▀ half-block characters.

    Two rows of pixels are packed into one terminal line:
      top pixel  → foreground color of ▀
      bottom pixel → background color of ▀

    Terminal cells are ~2:1 height-to-width, so this produces approximately
    square "pixels" in the preview.
    """
    height = len(pixels)
    width = len(pixels[0]) if pixels else 0
    lines = []

    for row_idx in range(0, height, 2):
        top_row = pixels[row_idx]
        bot_row = pixels[row_idx + 1] if row_idx + 1 < height else ["#000000"] * width

        parts = []
        for col_idx in range(width):
            tr, tg, tb = hex_to_rgb(top_row[col_idx])
            br, bg, bb = hex_to_rgb(bot_row[col_idx])
            parts.append(
                f"\033[38;2;{tr};{tg};{tb}m"   # fg = top pixel
                f"\033[48;2;{br};{bg};{bb}m"   # bg = bottom pixel
                "▀"
            )
        lines.append("".join(parts) + RESET)

    print("\n".join(lines))
