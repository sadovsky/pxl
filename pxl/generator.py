import json
import os
import re

import anthropic
import click

from pxl.utils import hex_to_rgb, is_valid_hex_color

SYSTEM_PROMPT = """\
You are a pixel art generator. When given a description, you respond ONLY with a JSON \
object — no markdown fences, no explanation, no text before or after.

The JSON object must have exactly this shape:
{
  "width": <integer>,
  "height": <integer>,
  "pixels": [
    ["#RRGGBB", "#RRGGBB", ...],
    ...
  ]
}

Format rules:
- pixels is an array of exactly `height` arrays, each containing exactly `width` hex color strings.
- Each color is exactly 7 characters: a # followed by 6 uppercase hex digits (e.g. "#FF0000").
- Use "#000000" for transparent/background pixels only.
- Never include comments, trailing commas, or any non-JSON text in your response.

Pixel art aesthetics — follow these carefully:
1. SILHOUETTE FIRST. Design a clear, readable outline of the subject that fills most of the canvas \
(leave only a 1–2 pixel margin). The silhouette should be identifiable at a glance.
2. OUTLINE LAYER. Draw a solid 1-pixel dark outline (e.g. "#111111") around the entire sprite and \
between major color regions. This is the single most important factor in making pixel art look clean.
3. LIMITED PALETTE. Use 6–14 colors total. One base color per region, one highlight (lighter), one \
shadow (darker). Avoid random or near-duplicate colors.
4. SHADING. Add at least one highlight and one shadow tone to major surfaces. Light comes from the \
upper-left: highlights on upper-left edges, shadows on lower-right edges.
5. NO NOISE. Every pixel must belong to a recognizable region (outline, fill, highlight, shadow, or \
background). Do not scatter single isolated pixels of unrelated colors.
6. CONTRAST. The sprite must contrast strongly against the #000000 background. Avoid dark colors for \
the main body unless the subject is inherently dark.
7. CENTERING. Center the sprite both horizontally and vertically. The subject should occupy at least \
70% of the canvas width and height.\
"""


def _get_client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise click.ClickException(
            "ANTHROPIC_API_KEY environment variable is not set.\n"
            "Export it in your shell:  export ANTHROPIC_API_KEY=sk-ant-..."
        )
    return anthropic.Anthropic(api_key=key)


def _build_user_message(description: str, width: int, height: int) -> str:
    return (
        f"Create a {width}x{height} pixel art sprite of: {description}\n\n"
        f"Grid: exactly {width} columns wide and {height} rows tall.\n"
        f"Style: classic game sprite aesthetic — clear silhouette, dark outline, "
        f"limited palette, shading from upper-left light source."
    )


def _extract_json_object(text: str) -> str:
    """Return the first balanced {...} substring found in text."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


def _parse_response(raw: str) -> dict:
    # Strip potential markdown code fences despite instructions
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)
    else:
        raw = _extract_json_object(raw)
    return json.loads(raw)


def _validate_grid(data: dict, expected_width: int, expected_height: int) -> None:
    pixels = data.get("pixels")
    if not isinstance(pixels, list):
        raise ValueError("'pixels' key missing or not a list")
    if len(pixels) != expected_height:
        raise ValueError(f"Expected {expected_height} rows, got {len(pixels)}")
    for i, row in enumerate(pixels):
        if not isinstance(row, list) or len(row) != expected_width:
            got = len(row) if isinstance(row, list) else "non-list"
            raise ValueError(f"Row {i} has {got} pixels, expected {expected_width}")
        for j, color in enumerate(row):
            if not isinstance(color, str) or not is_valid_hex_color(color):
                raise ValueError(f"Invalid color at [{i}][{j}]: {color!r}")


ANIMATION_SYSTEM_PROMPT = """\
You are a pixel art animator. When given a description and a frame count, you respond ONLY with a \
JSON object — no markdown fences, no explanation, no text before or after.

The JSON object must have exactly this shape:
{
  "width": <integer>,
  "height": <integer>,
  "frame_count": <integer>,
  "frames": [
    [["#RRGGBB", "#RRGGBB", ...], ...],
    [["#RRGGBB", "#RRGGBB", ...], ...],
    ...
  ]
}

Format rules:
- frames is an array of exactly `frame_count` grids.
- Each grid is an array of exactly `height` arrays, each containing exactly `width` hex color strings.
- Each color is exactly 7 characters: a # followed by 6 uppercase hex digits (e.g. "#FF0000").
- Use "#000000" for transparent/background pixels only.
- Never include comments, trailing commas, or any non-JSON text in your response.

Pixel art aesthetics — follow these carefully:
1. SILHOUETTE FIRST. Design a clear, readable outline of the subject that fills most of the canvas \
(leave only a 1–2 pixel margin). The silhouette should be identifiable at a glance.
2. OUTLINE LAYER. Draw a solid 1-pixel dark outline (e.g. "#111111") around the entire sprite and \
between major color regions. This is the single most important factor in making pixel art look clean.
3. LIMITED PALETTE. Use 6–14 colors total. One base color per region, one highlight (lighter), one \
shadow (darker). Avoid random or near-duplicate colors.
4. SHADING. Add at least one highlight and one shadow tone to major surfaces. Light comes from the \
upper-left: highlights on upper-left edges, shadows on lower-right edges.
5. NO NOISE. Every pixel must belong to a recognizable region (outline, fill, highlight, shadow, or \
background). Do not scatter single isolated pixels of unrelated colors.
6. CONTRAST. The sprite must contrast strongly against the #000000 background. Avoid dark colors for \
the main body unless the subject is inherently dark.
7. CENTERING. Center the sprite both horizontally and vertically. The subject should occupy at least \
70% of the canvas width and height.

Animation rules:
- Use the SAME color palette across ALL frames — the character/object must look consistent.
- Keep the same overall proportions in every frame; only move or deform the parts that are animating.
- Each frame should show a clear, distinct animation step (e.g. walk cycle, idle bob, spin rotation).
- The animation must loop smoothly: the last frame transitions naturally back to the first.
- Do not introduce new colors or outline styles in later frames.\
"""


def _validate_animation(
    data: dict,
    expected_width: int,
    expected_height: int,
    expected_frames: int,
) -> None:
    frames = data.get("frames")
    if not isinstance(frames, list):
        raise ValueError("'frames' key missing or not a list")
    if len(frames) != expected_frames:
        raise ValueError(f"Expected {expected_frames} frames, got {len(frames)}")
    for f_idx, frame in enumerate(frames):
        if not isinstance(frame, list) or len(frame) != expected_height:
            got = len(frame) if isinstance(frame, list) else "non-list"
            raise ValueError(f"Frame {f_idx} has {got} rows, expected {expected_height}")
        for i, row in enumerate(frame):
            if not isinstance(row, list) or len(row) != expected_width:
                got = len(row) if isinstance(row, list) else "non-list"
                raise ValueError(
                    f"Frame {f_idx} row {i} has {got} pixels, expected {expected_width}"
                )
            for j, color in enumerate(row):
                if not isinstance(color, str) or not is_valid_hex_color(color):
                    raise ValueError(
                        f"Invalid color at frame {f_idx}[{i}][{j}]: {color!r}"
                    )


def generate_animation_frames(
    description: str,
    width: int = 16,
    height: int = 16,
    n_frames: int = 4,
    model: str = "claude-sonnet-4-6",
    max_retries: int = 2,
) -> list[list[list[str]]]:
    client = _get_client()
    max_tokens = max(2048, width * height * n_frames * 12)
    user_msg = (
        f"Create a {n_frames}-frame animation of: {description}\n\n"
        f"Each frame must be exactly {width} columns wide and {height} rows tall.\n"
        f"frame_count must be exactly {n_frames}."
    )

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=ANIMATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
        except anthropic.APIStatusError as exc:
            raise click.ClickException(f"API error {exc.status_code}: {exc.message}")
        except anthropic.APIConnectionError:
            raise click.ClickException("Network error: could not reach the Anthropic API.")
        except anthropic.RateLimitError:
            raise click.ClickException("Rate limit reached. Wait a moment and try again.")

        raw = response.content[0].text.strip()

        try:
            data = _parse_response(raw)
            _validate_animation(data, width, height, n_frames)
            return data["frames"]
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            if attempt == max_retries:
                raise click.ClickException(
                    f"Claude returned invalid animation data after {max_retries + 1} attempts.\n"
                    f"Last error: {exc}\nRaw response (first 500 chars):\n{raw[:500]}"
                )


def generate_pixel_grid(
    description: str,
    width: int = 16,
    height: int = 16,
    model: str = "claude-sonnet-4-6",
    max_retries: int = 2,
) -> list[list[str]]:
    client = _get_client()
    # Ensure enough tokens for the full grid: each cell is ~10 chars + overhead
    max_tokens = max(1024, width * height * 12)

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": _build_user_message(description, width, height)}
                ],
            )
        except anthropic.APIStatusError as exc:
            raise click.ClickException(f"API error {exc.status_code}: {exc.message}")
        except anthropic.APIConnectionError:
            raise click.ClickException("Network error: could not reach the Anthropic API.")
        except anthropic.RateLimitError:
            raise click.ClickException("Rate limit reached. Wait a moment and try again.")

        raw = response.content[0].text.strip()

        try:
            data = _parse_response(raw)
            _validate_grid(data, width, height)
            return data["pixels"]
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            if attempt == max_retries:
                raise click.ClickException(
                    f"Claude returned invalid pixel data after {max_retries + 1} attempts.\n"
                    f"Last error: {exc}\nRaw response (first 500 chars):\n{raw[:500]}"
                )
