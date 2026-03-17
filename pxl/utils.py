import re

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
TRANSPARENT = "#000000"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def is_valid_hex_color(color: str) -> bool:
    return bool(HEX_COLOR_RE.match(color))
