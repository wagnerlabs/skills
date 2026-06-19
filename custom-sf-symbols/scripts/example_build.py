#!/usr/bin/env python3
"""
example_build.py — worked example that builds a custom SF Symbol end to end with the
helpers in sfsymbol_lib.py. Copy this file and edit build_weight() to make your own.

This example reproduces a "proportional.sizing" glyph: two stacked hollow rounded
rectangles in the style of Apple's `rectangle.grid.1x2`, but the top cell is taller and
the bottom cell shorter (a 2:1 split), keeping the same footprint per weight.

The per-weight PARAMS below were MEASURED from the real `rectangle.grid.1x2` with
render_reference.swift + measure.py (values in template units). When matching a different
base symbol, re-measure and replace these numbers.

Run:  python3 example_build.py [output_dir]   (default: ./out)
Then render previews:
      ./svg2png out/preview_Regular.svg out/preview_Regular.png 480
"""
import os
import sys
import sfsymbol_lib as sf

# Measured from rectangle.grid.1x2 (template units). S=stroke, W=width, H=total height,
# gap=space between the two cells, Ro=outer corner radius.
PARAMS = {
    "Ultralight": dict(S=2.5,  W=103.0, H=85.5,  gap=9.0, Ro=4.8),
    "Regular":    dict(S=7.5,  W=105.5, H=90.2,  gap=8.0, Ro=9.0),
    "Black":      dict(S=17.2, W=123.8, H=110.5, gap=5.5, Ro=13.5),
}
TOP_FRAC = 0.6667   # top cell's share of the available cell height -> ~2:1
MIN_HOLE = 7.0      # keep the small cell hollow at heavy weights (Black would fill solid)


def build_weight(weight):
    """Return (paths, bbox) for one weight, in design space (y-down, x centered on 0)."""
    p = PARAMS[weight]
    S, W, H, gap, Ro = p["S"], p["W"], p["H"], p["gap"], p["Ro"]
    avail = H - gap
    big = TOP_FRAC * avail
    small = avail - big
    min_small = 2 * S + MIN_HOLE          # clamp so the thin cell keeps a visible hole
    if small < min_small:
        small = min_small
        big = avail - small
    topH, botH = big, small               # big on top; swap for the "small on top" variant
    hw = W / 2.0
    top_cy = topH / 2.0
    bot_cy = topH + gap + botH / 2.0
    paths = [
        sf.ring(0, top_cy, hw, topH / 2.0, S, Ro),
        sf.ring(0, bot_cy, hw, botH / 2.0, S, Ro),
    ]
    return paths, (-hw, 0.0, hw, H)        # explicit bbox (do not trust bbox() for arcs)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "out"
    os.makedirs(out_dir, exist_ok=True)
    name = "proportional.sizing"

    weight_paths = {w: build_weight(w) for w in sf.WEIGHTS}

    svg = sf.assemble_template(name, weight_paths)
    ss = sf.write_symbolset(out_dir, name, svg)
    print("wrote", ss)

    # standalone previews for rasterizing with svg2png
    for w in sf.WEIGHTS:
        paths, box = weight_paths[w]
        with open(os.path.join(out_dir, f"preview_{w}.svg"), "w") as f:
            f.write(sf.preview_svg(paths, box))
    print("wrote previews to", out_dir)


if __name__ == "__main__":
    main()
