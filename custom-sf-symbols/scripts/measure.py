#!/usr/bin/env python3
"""
measure.py — measure stroke width, ink dimensions, and corner radii from a rendered PNG
(black-on-transparent), so a custom glyph can match a real SF Symbol's metrics.

Requires Pillow:  python3 -m pip install --user Pillow

Usage:
  python3 measure.py <file.png> [--scale N]
    --scale N : pixels per template unit (default 4, i.e. rendered at 400 for a 100pt template).
                Reported values are divided by N to give template units in parentheses.

Reads:
  - ink bbox + W x H
  - vertical run lengths through the horizontal center (each = a horizontal stroke/border)
  - horizontal run lengths through the vertical center (each = a vertical stroke/border)
  - outer corner radius of the top-left-most shape (depth until the top edge reaches full width)

Interpret: a hollow rounded rectangle shows 2 vertical runs at center (top & bottom borders)
whose length = stroke; outer corner R is the rounding; inner R ~= outer R - 0.7*stroke.
"""
import sys
from PIL import Image

THR = 128


def load(p):
    im = Image.open(p).convert("RGBA")
    return im.size[0], im.size[1], im.load()


def runs(on_at, n):
    out, s = [], None
    for i in range(n):
        on = on_at(i)
        if on and s is None:
            s = i
        if (not on) and s is not None:
            out.append((s, i - 1, i - s)); s = None
    if s is not None:
        out.append((s, n - 1, n - s))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    path = sys.argv[1]
    scale = 4.0
    if "--scale" in sys.argv:
        scale = float(sys.argv[sys.argv.index("--scale") + 1])
    W, H, px = load(path)
    A = lambda x, y: px[x, y][3]
    ink = [(x, y) for y in range(H) for x in range(W) if A(x, y) >= THR]
    if not ink:
        print("no ink found"); sys.exit(2)
    xs = [p[0] for p in ink]; ys = [p[1] for p in ink]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    iw, ih = maxx - minx + 1, maxy - miny + 1
    cx, cy = (minx + maxx) // 2, (miny + maxy) // 2
    u = lambda v: f"{v}({v/scale:.1f})"
    print(f"{path}: canvas {W}x{H}  INK {u(iw)} x {u(ih)}  x[{minx}..{maxx}] y[{miny}..{maxy}]")
    vr = runs(lambda y: A(cx, y) >= THR, H)
    hr = runs(lambda x: A(x, cy) >= THR, W)
    print("  vertical runs @center-x (horizontal strokes): " + ", ".join(u(r[2]) for r in vr))
    print("  horizontal runs @center-y (vertical strokes):  " + ", ".join(u(r[2]) for r in hr))

    def leftmost(y):
        for x in range(W):
            if A(x, y) >= THR:
                return x
        return None
    y = miny
    while y < maxy and (leftmost(y) or minx) > minx:
        y += 1
    print(f"  outer corner R (top-left) ~= {u(y - miny)}")


if __name__ == "__main__":
    main()
