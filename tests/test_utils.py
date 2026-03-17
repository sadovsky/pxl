import pytest

from pxl.utils import hex_to_rgb, is_valid_hex_color


# --- hex_to_rgb ---

def test_hex_to_rgb_red():
    assert hex_to_rgb("#FF0000") == (255, 0, 0)

def test_hex_to_rgb_green():
    assert hex_to_rgb("#00FF00") == (0, 255, 0)

def test_hex_to_rgb_blue():
    assert hex_to_rgb("#0000FF") == (0, 0, 255)

def test_hex_to_rgb_black():
    assert hex_to_rgb("#000000") == (0, 0, 0)

def test_hex_to_rgb_white():
    assert hex_to_rgb("#FFFFFF") == (255, 255, 255)

def test_hex_to_rgb_mixed():
    assert hex_to_rgb("#1A2B3C") == (0x1A, 0x2B, 0x3C)

def test_hex_to_rgb_lowercase():
    assert hex_to_rgb("#aabbcc") == (0xAA, 0xBB, 0xCC)


# --- is_valid_hex_color ---

def test_valid_uppercase():
    assert is_valid_hex_color("#FF0000") is True

def test_valid_lowercase():
    assert is_valid_hex_color("#aabbcc") is True

def test_valid_mixed_case():
    assert is_valid_hex_color("#AbCdEf") is True

def test_valid_black():
    assert is_valid_hex_color("#000000") is True

def test_invalid_short():
    assert is_valid_hex_color("#FFF") is False

def test_invalid_no_hash():
    assert is_valid_hex_color("FF0000") is False

def test_invalid_too_long():
    assert is_valid_hex_color("#FF000000") is False

def test_invalid_name():
    assert is_valid_hex_color("red") is False

def test_invalid_special_chars():
    assert is_valid_hex_color("#GG0000") is False
