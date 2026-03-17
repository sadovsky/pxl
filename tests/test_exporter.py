import pytest
from pathlib import Path
from PIL import Image

from pxl.exporter import save_png


def _make_grid(rows, cols, color="#FF0000"):
    return [[color] * cols for _ in range(rows)]


def test_output_dimensions(tmp_path):
    out = tmp_path / "out.png"
    save_png(_make_grid(4, 8), out, scale=8)
    img = Image.open(out)
    assert img.size == (8 * 8, 4 * 8)  # (width*scale, height*scale)


def test_default_scale_dimensions(tmp_path):
    out = tmp_path / "out.png"
    save_png(_make_grid(16, 16), out)
    img = Image.open(out)
    assert img.size == (256, 256)


def test_black_pixels_are_transparent(tmp_path):
    out = tmp_path / "out.png"
    save_png([["#000000"]], out, scale=4)
    img = Image.open(out).convert("RGBA")
    r, g, b, a = img.getpixel((0, 0))
    assert a == 0


def test_non_black_pixels_are_opaque(tmp_path):
    out = tmp_path / "out.png"
    save_png([["#FF0000"]], out, scale=4)
    img = Image.open(out).convert("RGBA")
    r, g, b, a = img.getpixel((0, 0))
    assert (r, g, b, a) == (255, 0, 0, 255)


def test_correct_color_written(tmp_path):
    out = tmp_path / "out.png"
    save_png([["#1A2B3C"]], out, scale=2)
    img = Image.open(out).convert("RGBA")
    r, g, b, a = img.getpixel((0, 0))
    assert (r, g, b) == (0x1A, 0x2B, 0x3C)


def test_creates_parent_directory(tmp_path):
    out = tmp_path / "nested" / "deep" / "out.png"
    assert not out.parent.exists()
    save_png(_make_grid(2, 2), out, scale=4)
    assert out.exists()


def test_rgba_mode(tmp_path):
    out = tmp_path / "out.png"
    save_png(_make_grid(2, 2), out, scale=4)
    img = Image.open(out)
    assert img.mode == "RGBA"
