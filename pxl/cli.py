import json
import re
from pathlib import Path

import click

from pxl import __version__
from pxl import generator, renderer, exporter


@click.group()
@click.version_option(__version__, prog_name="pxl")
def cli():
    """pxl — pixel art generator powered by Claude."""
    pass


@cli.command()
@click.argument("description")
@click.option(
    "--size", "-s",
    default="16x16",
    show_default=True,
    help="Grid dimensions as WxH (e.g. 16x16, 32x32).",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output PNG file path (default: <slugified-description>.png).",
)
@click.option(
    "--scale",
    default=16,
    show_default=True,
    type=int,
    help="Physical pixels per grid cell in the exported PNG.",
)
@click.option(
    "--no-preview",
    is_flag=True,
    default=False,
    help="Skip terminal preview.",
)
@click.option(
    "--model",
    default="claude-3-5-haiku-20241022",
    show_default=True,
    help="Claude model to use (e.g. claude-3-5-sonnet-20241022).",
)
@click.option(
    "--json", "save_json",
    default=None,
    metavar="FILE",
    help="Also save the pixel grid as a JSON file.",
)
def generate(description, size, output, scale, no_preview, model, save_json):
    """Generate pixel art from a text DESCRIPTION.

    \b
    Examples:
      pxl generate "a small red mushroom"
      pxl generate "a blue spaceship" --size 32x32 --output ship.png
      pxl generate "a golden coin" --scale 32 --no-preview
    """
    try:
        width, height = _parse_size(size)
    except ValueError:
        raise click.BadParameter(
            f"Must be WxH (e.g. 16x16, 32x32), got: {size!r}",
            param_hint="--size",
        )

    if output is None:
        output = _slugify(description) + ".png"

    click.echo(f"Generating {width}x{height} pixel art: {description!r} ...")

    pixels = generator.generate_pixel_grid(description, width, height, model)

    if not no_preview:
        renderer.print_preview(pixels)

    exporter.save_png(pixels, output, scale=scale)
    click.echo(click.style(f"Saved → {output}  ({width * scale}×{height * scale}px)", fg="green"))

    if save_json:
        data = {"width": width, "height": height, "pixels": pixels}
        Path(save_json).write_text(json.dumps(data, indent=2))
        click.echo(click.style(f"Saved → {save_json}  (JSON grid)", fg="green"))


def _parse_size(size_str: str) -> tuple[int, int]:
    parts = size_str.lower().split("x")
    if len(parts) != 2:
        raise ValueError
    w, h = int(parts[0]), int(parts[1])
    if w < 1 or h < 1 or w > 128 or h > 128:
        raise ValueError
    return w, h


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:40] or "pixel-art"
