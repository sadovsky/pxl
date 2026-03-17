import json
import pytest

from pxl.generator import _parse_response, _validate_grid, _validate_animation


# --- _parse_response ---

def test_parse_response_plain_json():
    raw = '{"width": 2, "height": 2, "pixels": [["#FF0000","#00FF00"],["#0000FF","#FFFFFF"]]}'
    result = _parse_response(raw)
    assert result["width"] == 2
    assert result["pixels"][0][0] == "#FF0000"


def test_parse_response_strips_json_fences():
    raw = '```json\n{"pixels": [["#000000"]]}\n```'
    result = _parse_response(raw)
    assert result["pixels"] == [["#000000"]]


def test_parse_response_strips_plain_fences():
    raw = '```\n{"pixels": [["#AABBCC"]]}\n```'
    result = _parse_response(raw)
    assert result["pixels"] == [["#AABBCC"]]


def test_parse_response_extracts_json_from_prose():
    raw = 'Here is the output: {"pixels": [["#112233"]]} Hope that helps!'
    result = _parse_response(raw)
    assert result["pixels"] == [["#112233"]]


def test_parse_response_invalid_json_raises():
    with pytest.raises(json.JSONDecodeError):
        _parse_response("not json at all")


# --- _validate_grid ---

def _make_grid(rows: int, cols: int, color: str = "#ABCDEF") -> dict:
    return {"pixels": [[color] * cols for _ in range(rows)]}


def test_validate_grid_valid():
    data = _make_grid(2, 3)
    _validate_grid(data, expected_width=3, expected_height=2)  # should not raise


def test_validate_grid_wrong_row_count():
    data = _make_grid(3, 3)
    with pytest.raises(ValueError, match="Expected 2 rows"):
        _validate_grid(data, expected_width=3, expected_height=2)


def test_validate_grid_wrong_col_count():
    data = _make_grid(2, 2)
    with pytest.raises(ValueError, match="Row 0"):
        _validate_grid(data, expected_width=3, expected_height=2)


def test_validate_grid_missing_pixels_key():
    with pytest.raises(ValueError, match="'pixels' key missing"):
        _validate_grid({"width": 2, "height": 2}, expected_width=2, expected_height=2)


def test_validate_grid_bad_color_format():
    data = {"pixels": [["red", "#00FF00"], ["#0000FF", "#FFFFFF"]]}
    with pytest.raises(ValueError, match=r"Invalid color at \[0\]\[0\]"):
        _validate_grid(data, expected_width=2, expected_height=2)


def test_validate_grid_lowercase_hex_accepted():
    data = {"pixels": [["#aabbcc"]]}
    _validate_grid(data, expected_width=1, expected_height=1)  # should not raise


def test_validate_grid_short_hex_rejected():
    data = {"pixels": [["#FFF"]]}
    with pytest.raises(ValueError, match="Invalid color"):
        _validate_grid(data, expected_width=1, expected_height=1)


# --- _validate_animation ---

def _make_animation(n_frames: int, rows: int, cols: int, color: str = "#ABCDEF") -> dict:
    frames = [[[color] * cols for _ in range(rows)] for _ in range(n_frames)]
    return {"width": cols, "height": rows, "frame_count": n_frames, "frames": frames}


def test_validate_animation_valid():
    data = _make_animation(4, 2, 3)
    _validate_animation(data, expected_width=3, expected_height=2, expected_frames=4)


def test_validate_animation_missing_frames_key():
    with pytest.raises(ValueError, match="'frames' key missing"):
        _validate_animation({"width": 2}, expected_width=2, expected_height=2, expected_frames=3)


def test_validate_animation_wrong_frame_count():
    data = _make_animation(3, 2, 2)
    with pytest.raises(ValueError, match="Expected 4 frames"):
        _validate_animation(data, expected_width=2, expected_height=2, expected_frames=4)


def test_validate_animation_frame_wrong_row_count():
    data = _make_animation(2, 3, 2)  # 3 rows per frame
    with pytest.raises(ValueError, match="Frame 0"):
        _validate_animation(data, expected_width=2, expected_height=2, expected_frames=2)


def test_validate_animation_frame_wrong_col_count():
    data = _make_animation(2, 2, 3)  # 3 cols per row
    with pytest.raises(ValueError, match="row 0"):
        _validate_animation(data, expected_width=2, expected_height=2, expected_frames=2)


def test_validate_animation_bad_color_in_frame():
    data = _make_animation(2, 1, 1)
    data["frames"][1][0][0] = "bad"
    with pytest.raises(ValueError, match="Invalid color at frame 1"):
        _validate_animation(data, expected_width=1, expected_height=1, expected_frames=2)
