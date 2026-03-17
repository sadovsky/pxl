# pxl

CLI pixel art generator powered by Claude. Describe a sprite in plain English, get a terminal preview and a PNG.

```
pxl generate "a small red mushroom"
```

## Install

```bash
git clone https://github.com/sadovsky/pxl
cd pxl
pip install -e .
```

## Setup

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or add it to a .env file:
cp .env.example .env
```

## Usage

```
pxl generate DESCRIPTION [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-s, --size WxH` | `16x16` | Grid dimensions, e.g. `8x8`, `32x32` |
| `-o, --output FILE` | `<slug>.png` | Output PNG path |
| `--scale N` | `16` | Physical pixels per grid cell (e.g. `--scale 32` → 512×512 for a 16×16 grid) |
| `--no-preview` | off | Skip the terminal preview |

### Examples

```bash
# 16x16 sprite, terminal preview + PNG saved as "small-red-mushroom.png"
pxl generate "a small red mushroom"

# 32x32, custom output path
pxl generate "a blue spaceship" --size 32x32 --output ship.png

# High-res PNG, no preview
pxl generate "a golden coin" --scale 32 --no-preview
```

## Output

- **Terminal**: ANSI true-color preview using `▀` half-block characters
- **PNG**: RGBA image — `#000000` pixels are transparent, ready for use in game engines

## Development

```bash
pip install -e ".[dev]"
pytest
```
