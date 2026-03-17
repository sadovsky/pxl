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

Rules:
- pixels is an array of exactly `height` arrays, each containing exactly `width` hex color strings.
- Each color is exactly 7 characters: a # followed by 6 uppercase hex digits (e.g. "#FF0000").
- Use "#000000" for transparent/background pixels.
- Fill the sprite within the grid — do not pad with large empty borders.
- The art should be recognizable at the requested size.
- Never include comments, trailing commas, or any non-JSON text in your response.\
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
        f"The grid must be exactly {width} columns wide and {height} rows tall."
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


def generate_pixel_grid(
    description: str,
    width: int = 16,
    height: int = 16,
    model: str = "claude-3-5-haiku-20241022",
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
