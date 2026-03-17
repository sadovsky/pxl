import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pxl.cli import cli, _parse_size, _slugify


# --- _parse_size ---

def test_parse_size_standard():
    assert _parse_size("16x16") == (16, 16)

def test_parse_size_non_square():
    assert _parse_size("32x8") == (32, 8)

def test_parse_size_uppercase():
    assert _parse_size("16X16") == (16, 16)

def test_parse_size_min():
    assert _parse_size("1x1") == (1, 1)

def test_parse_size_max():
    assert _parse_size("128x128") == (128, 128)

def test_parse_size_too_wide():
    with pytest.raises(ValueError):
        _parse_size("129x16")

def test_parse_size_zero():
    with pytest.raises(ValueError):
        _parse_size("0x16")

def test_parse_size_no_separator():
    with pytest.raises(ValueError):
        _parse_size("1616")

def test_parse_size_non_numeric():
    with pytest.raises(ValueError):
        _parse_size("axb")


# --- _slugify ---

def test_slugify_basic():
    assert _slugify("a small red mushroom") == "a-small-red-mushroom"

def test_slugify_special_chars():
    assert _slugify("hello, world!") == "hello-world"

def test_slugify_multiple_spaces():
    assert _slugify("a  b") == "a-b"

def test_slugify_truncates_at_40():
    long = "a" * 50
    assert len(_slugify(long)) == 40

def test_slugify_empty_falls_back():
    assert _slugify("!!!") == "pixel-art"

def test_slugify_uppercase():
    assert _slugify("RED STAR") == "red-star"


# --- generate command ---

FAKE_GRID = [["#FF0000", "#00FF00"], ["#0000FF", "#FFFFFF"]]


def _run_generate(args, mock_grid=FAKE_GRID):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch("pxl.generator.generate_pixel_grid", return_value=mock_grid), \
             patch("pxl.renderer.print_preview") as mock_preview, \
             patch("pxl.exporter.save_png") as mock_save:
            result = runner.invoke(cli, ["generate"] + args)
    return result, mock_preview, mock_save


def test_generate_basic_success():
    result, _, mock_save = _run_generate(["a red square", "--no-preview"])
    assert result.exit_code == 0
    assert "Saved" in result.output
    mock_save.assert_called_once()


def test_generate_calls_preview_by_default():
    result, mock_preview, _ = _run_generate(["a red square"])
    assert result.exit_code == 0
    mock_preview.assert_called_once_with(FAKE_GRID)


def test_generate_no_preview_skips_renderer():
    result, mock_preview, _ = _run_generate(["a red square", "--no-preview"])
    assert result.exit_code == 0
    mock_preview.assert_not_called()


def test_generate_custom_output():
    result, _, mock_save = _run_generate(["a red square", "--no-preview", "-o", "custom.png"])
    assert result.exit_code == 0
    call_path = str(mock_save.call_args[0][1])
    assert call_path == "custom.png"


def test_generate_custom_scale():
    result, _, mock_save = _run_generate(["a red square", "--no-preview", "--scale", "32"])
    assert result.exit_code == 0
    assert mock_save.call_args[1]["scale"] == 32


def test_generate_invalid_size():
    result, _, _ = _run_generate(["a red square", "--size", "bad"])
    assert result.exit_code != 0
    assert "WxH" in result.output


def test_generate_saves_json(tmp_path):
    runner = CliRunner()
    json_path = str(tmp_path / "out.json")
    with patch("pxl.generator.generate_pixel_grid", return_value=FAKE_GRID), \
         patch("pxl.renderer.print_preview"), \
         patch("pxl.exporter.save_png"):
        result = runner.invoke(cli, [
            "generate", "a red square", "--no-preview", "--size", "2x2", "--json", json_path
        ])
    assert result.exit_code == 0
    data = json.loads(Path(json_path).read_text())
    assert data["pixels"] == FAKE_GRID
    assert data["width"] == 2
    assert data["height"] == 2


def test_generate_default_output_slug():
    result, _, mock_save = _run_generate(["hello world", "--no-preview"])
    assert result.exit_code == 0
    call_path = str(mock_save.call_args[0][1])
    assert call_path == "hello-world.png"
