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
    default="claude-haiku-4-5-20251001",
    show_default=True,
    help="Claude model to use (e.g. claude-sonnet-4-6).",
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


@cli.command()
@click.argument("description")
@click.option(
    "--frames", "-n",
    default=4,
    show_default=True,
    type=int,
    help="Number of animation frames to generate.",
)
@click.option(
    "--fps",
    default=8,
    show_default=True,
    type=int,
    help="Frames per second in the output animation.",
)
@click.option(
    "--size", "-s",
    default="16x16",
    show_default=True,
    help="Grid dimensions as WxH (e.g. 16x16, 32x32).",
)
@click.option(
    "--scale",
    default=16,
    show_default=True,
    type=int,
    help="Physical pixels per grid cell in the exported image.",
)
@click.option(
    "--format", "fmt",
    default="gif",
    show_default=True,
    type=click.Choice(["gif", "apng"], case_sensitive=False),
    help="Output animation format.",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output file path (default: <slugified-description>.<format>).",
)
@click.option(
    "--sheet",
    default=None,
    metavar="FILE",
    help="Also save a sprite sheet PNG with all frames.",
)
@click.option(
    "--columns",
    default=None,
    type=int,
    metavar="N",
    help="Columns in the sprite sheet (default: all frames in one row).",
)
@click.option(
    "--no-preview",
    is_flag=True,
    default=False,
    help="Skip terminal preview.",
)
@click.option(
    "--model",
    default="claude-haiku-4-5-20251001",
    show_default=True,
    help="Claude model to use.",
)
def animate(description, frames, fps, size, scale, fmt, output, sheet, columns, no_preview, model):
    """Generate an animated pixel art sprite from a text DESCRIPTION.

    \b
    Examples:
      pxl animate "a walking character"
      pxl animate "a spinning coin" --frames 8 --format apng --sheet coin-sheet.png
      pxl animate "an exploding bomb" --frames 6 --fps 12 --size 32x32
    """
    try:
        width, height = _parse_size(size)
    except ValueError:
        raise click.BadParameter(
            f"Must be WxH (e.g. 16x16, 32x32), got: {size!r}",
            param_hint="--size",
        )

    if output is None:
        output = _slugify(description) + "." + fmt.lower()

    click.echo(
        f"Generating {frames}-frame {width}x{height} animation: {description!r} ..."
    )

    pixel_frames = generator.generate_animation_frames(
        description, width, height, frames, model
    )

    if not no_preview:
        for i, frame in enumerate(pixel_frames):
            click.echo(f"── Frame {i + 1}/{frames} ──")
            renderer.print_preview(frame)

    if fmt.lower() == "apng":
        exporter.save_apng(pixel_frames, output, scale=scale, fps=fps)
    else:
        exporter.save_gif(pixel_frames, output, scale=scale, fps=fps)

    click.echo(
        click.style(
            f"Saved → {output}  ({frames} frames @ {fps}fps, {width * scale}×{height * scale}px each)",
            fg="green",
        )
    )

    if sheet:
        exporter.save_sprite_sheet(pixel_frames, sheet, scale=scale, columns=columns)
        n_cols = min(columns, frames) if columns else frames
        import math
        n_rows = math.ceil(frames / n_cols)
        click.echo(
            click.style(
                f"Saved → {sheet}  ({n_cols * width * scale}×{n_rows * height * scale}px sprite sheet)",
                fg="green",
            )
        )


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
