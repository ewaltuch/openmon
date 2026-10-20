"""
Convert an SVG into a 4-shade Game Boy PNG for Open-Mon.

Usage: python scripts/svg2gb.py input.svg output.png [size]

size defaults to 32 (battle mascots); use 8 for overworld sprites.
Transparent areas become the lightest shade. Needs cairosvg (`.[tools]`).
"""

import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image  # noqa: E402

from src.constants import GB_PALETTE  # noqa: E402


def quantize(img):
    """Map any image to the 4 GB palette colors by brightness (alpha -> white)."""
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    gray = Image.alpha_composite(bg, rgba).convert("L")
    out = Image.new("RGB", gray.size)
    out.putdata([GB_PALETTE[3 - min(3, v // 64)] for v in gray.getdata()])
    return out


def svg_to_gb_png(svg_path, png_path, size=32):
    import cairosvg

    png_bytes = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)
    quantize(Image.open(io.BytesIO(png_bytes))).save(png_path)


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python scripts/svg2gb.py input.svg output.png [size]")
        sys.exit(1)
    svg_to_gb_png(
        sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) == 4 else 32
    )
