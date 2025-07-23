"""
Convert SVG mascots to 4-shade 16x16 PNGs for Open-Mon.
Usage: python scripts/svg2gb.py input.svg output.png
"""
import sys
from PIL import Image, ImageOps
import cairosvg
from src.constants import GB_PALETTE

def svg_to_gb_png(svg_path, png_path):
    # Render SVG to PNG (RGBA)
    png_bytes = cairosvg.svg2png(url=svg_path, output_width=16, output_height=16)
    img = Image.open(io.BytesIO(png_bytes)).convert("L")
    # Quantize to 4 shades
    img = ImageOps.posterize(img, 2)
    img = img.convert("RGB")
    # Map to GB palette
    palette = sum(GB_PALETTE, ())
    img.putpalette(palette * 64)
    img = img.quantize(colors=4, method=2)
    img.save(png_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/svg2gb.py input.svg output.png")
        sys.exit(1)
    svg_to_gb_png(sys.argv[1], sys.argv[2])
