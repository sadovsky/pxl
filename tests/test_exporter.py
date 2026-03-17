import pytest
from pathlib import Path
from PIL import Image

from pxl.exporter import save_png, save_gif, save_apng, save_sprite_sheet


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


# --- animation helpers ---

COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#FFFFFF", "#888888"]

def _make_frames(n, rows=4, cols=4):
    """Create n frames with distinct colors so Pillow doesn't collapse duplicates."""
    return [_make_grid(rows, cols, COLORS[i % len(COLORS)]) for i in range(n)]


# --- save_gif ---

def test_save_gif_frame_count(tmp_path):
    out = tmp_path / "out.gif"
    save_gif(_make_frames(3), out, scale=4, fps=8)
    img = Image.open(out)
    assert img.n_frames == 3


def test_save_gif_dimensions(tmp_path):
    out = tmp_path / "out.gif"
    save_gif(_make_frames(2, rows=4, cols=8), out, scale=4, fps=8)
    img = Image.open(out)
    assert img.size == (8 * 4, 4 * 4)  # (cols*scale, rows*scale)


def test_save_gif_loops(tmp_path):
    out = tmp_path / "out.gif"
    save_gif(_make_frames(2), out, scale=4, fps=8)
    img = Image.open(out)
    assert img.info.get("loop") == 0  # 0 = infinite loop


def test_save_gif_creates_parent_dir(tmp_path):
    out = tmp_path / "sub" / "dir" / "out.gif"
    assert not out.parent.exists()
    save_gif(_make_frames(2), out, scale=4, fps=8)
    assert out.exists()


# --- save_apng ---

def test_save_apng_frame_count(tmp_path):
    out = tmp_path / "out.png"
    save_apng(_make_frames(4), out, scale=4, fps=8)
    img = Image.open(out)
    assert img.n_frames == 4


def test_save_apng_dimensions(tmp_path):
    out = tmp_path / "out.png"
    save_apng(_make_frames(2, rows=8, cols=4), out, scale=2, fps=8)
    img = Image.open(out)
    assert img.size == (4 * 2, 8 * 2)


def test_save_apng_preserves_transparency(tmp_path):
    out = tmp_path / "out.png"
    # Frame of all-transparent pixels
    save_apng([[["#000000"] * 2] * 2], out, scale=4, fps=8)
    img = Image.open(out).convert("RGBA")
    _, _, _, alpha = img.getpixel((0, 0))
    assert alpha == 0


def test_save_apng_creates_parent_dir(tmp_path):
    out = tmp_path / "sub" / "out.png"
    assert not out.parent.exists()
    save_apng(_make_frames(2), out, scale=4, fps=8)
    assert out.exists()


# --- save_sprite_sheet ---

def test_save_sprite_sheet_single_row_dimensions(tmp_path):
    out = tmp_path / "sheet.png"
    # 4 frames of 4×4, scale=2 → sheet = (4*4*2, 1*4*2) = (32, 8)
    save_sprite_sheet(_make_frames(4, rows=4, cols=4), out, scale=2)
    img = Image.open(out)
    assert img.size == (4 * 4 * 2, 1 * 4 * 2)


def test_save_sprite_sheet_two_column_wraps(tmp_path):
    out = tmp_path / "sheet.png"
    # 4 frames, 2 columns → 2 cols × 2 rows; frames 4×4 scale=2 → (2*4*2, 2*4*2) = (16, 16)
    save_sprite_sheet(_make_frames(4, rows=4, cols=4), out, scale=2, columns=2)
    img = Image.open(out)
    assert img.size == (2 * 4 * 2, 2 * 4 * 2)


def test_save_sprite_sheet_creates_parent_dir(tmp_path):
    out = tmp_path / "deep" / "sheet.png"
    assert not out.parent.exists()
    save_sprite_sheet(_make_frames(2), out, scale=4)
    assert out.exists()


def test_save_sprite_sheet_rgba(tmp_path):
    out = tmp_path / "sheet.png"
    save_sprite_sheet(_make_frames(2), out, scale=4)
    img = Image.open(out)
    assert img.mode == "RGBA"
