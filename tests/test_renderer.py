import pytest

from pxl.renderer import print_preview


def _capture(pixels, capsys):
    print_preview(pixels)
    return capsys.readouterr().out


def _make_grid(rows, cols, color="#FF0000"):
    return [[color] * cols for _ in range(rows)]


# --- line count ---

def test_even_height_line_count(capsys):
    out = _capture(_make_grid(4, 4), capsys)
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 2  # 4 rows → 2 terminal lines


def test_odd_height_line_count(capsys):
    out = _capture(_make_grid(3, 4), capsys)
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 2  # 3 rows → 2 terminal lines (last padded)


def test_single_row(capsys):
    out = _capture(_make_grid(1, 4), capsys)
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 1


def test_two_rows(capsys):
    out = _capture(_make_grid(2, 4), capsys)
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 1


# --- ANSI escape codes are present ---

def test_contains_ansi_escape(capsys):
    out = _capture(_make_grid(2, 2, "#FF0000"), capsys)
    assert "\033[" in out


def test_contains_half_block_char(capsys):
    out = _capture(_make_grid(2, 2), capsys)
    assert "▀" in out


# --- odd-height padding uses last row, not black ---

def test_odd_height_no_black_padding(capsys):
    """Last terminal line foreground/background should both be the last row color,
    not black (#000000 → 0;0;0 in ANSI)."""
    # Single red row — fg and bg should both be 255;0;0, not 0;0;0
    out = _capture(_make_grid(1, 1, "#FF0000"), capsys)
    assert "255;0;0m▀" in out          # fg (top) = red
    assert "48;2;255;0;0m" in out      # bg (bot) = red, not black
    assert "48;2;0;0;0m" not in out    # black background must NOT appear


# --- width ---

def test_each_line_has_correct_number_of_blocks(capsys):
    width = 5
    out = _capture(_make_grid(2, width), capsys)
    line = out.rstrip("\n").split("\n")[0]
    assert line.count("▀") == width
