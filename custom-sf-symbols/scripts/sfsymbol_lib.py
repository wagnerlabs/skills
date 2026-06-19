"""
sfsymbol_lib.py — building blocks for hand-authored custom SF Symbols.

Pure Python, no third-party deps. Emits filled-outline SVG paths (capsules and
rounded-rect rings), assembles them into an Apple "Template v.4.0" SVG, and writes
a .symbolset asset folder.

Coordinate model (design space):
  - Work in "template units" (the symbol is typeset at 100 points; cap height = 70.459).
  - y increases DOWNWARD, the same as SVG. Center glyphs horizontally on x = 0.
  - Everything is a FILLED outline (never a stroked path) so it exports cleanly.

Key idea for weights: keep the same centerlines / outer dimensions and only vary the
stroke. Provide three "key" weights (Ultralight / Regular / Black) at the Small scale;
the system interpolates every other weight and scale.
"""

import os
import re

# ---- canvas / guide constants (from Apple's Template v.4.0) ----
CANVAS = (3300, 2200)
BASELINE_S = 696.0
CAPLINE_S = 625.541              # cap height = BASELINE_S - CAPLINE_S = 70.459
CAPBAND = (CAPLINE_S + BASELINE_S) / 2.0          # 660.7705 — vertical center to align ink on
# x-center of each key-weight column in the Small row:
COLCENTER = {"Ultralight": 559.711, "Regular": 1449.84, "Black": 2933.4}
# class string so the symbol renders in monochrome / hierarchical / multicolor / preview:
CLS = "monochrome-1 multicolor-1:tintColor hierarchical-1:primary SFSymbolsPreview007AFF"

# Optional scaffold: if SF Symbols.app is installed we reuse Apple's exact Notes/Guides.
SCAFFOLD_DEFAULT = os.environ.get(
    "SF_SCAFFOLD",
    "/Applications/SF Symbols.app/Contents/Resources/badge.arrow.up.svg",
)

WEIGHTS = ["Ultralight", "Regular", "Black"]


def fmt(v):
    """Compact number formatting (ints stay int, floats trimmed to 3dp)."""
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.3f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- primitives
def capsule(p0, p1, r):
    """Filled stadium (round-capped thick segment) of half-width r between p0 and p1.
    Caps derive from geometry, so this is correct at any orientation."""
    import math
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-6:  # degenerate -> circle
        return (f"M {fmt(x0-r)},{fmt(y0)} A {fmt(r)},{fmt(r)} 0 1 0 {fmt(x0+r)},{fmt(y0)} "
                f"A {fmt(r)},{fmt(r)} 0 1 0 {fmt(x0-r)},{fmt(y0)} Z")
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    A = (x0 + nx * r, y0 + ny * r); B = (x1 + nx * r, y1 + ny * r)
    C = (x1 - nx * r, y1 - ny * r); D = (x0 - nx * r, y0 - ny * r)
    return (f"M {fmt(A[0])},{fmt(A[1])} L {fmt(B[0])},{fmt(B[1])} "
            f"A {fmt(r)},{fmt(r)} 0 0 0 {fmt(C[0])},{fmt(C[1])} L {fmt(D[0])},{fmt(D[1])} "
            f"A {fmt(r)},{fmt(r)} 0 0 0 {fmt(A[0])},{fmt(A[1])} Z")


def rrect(cx, cy, hw, hh, R, cw=True):
    """Rounded-rectangle outline. cw=True winds one way, False the other (use the
    opposite winding for an inner cutout so a single path forms a ring)."""
    R = min(R, hw, hh)
    l, r, t, b = cx - hw, cx + hw, cy - hh, cy + hh
    if cw:
        return (f"M {fmt(l+R)},{fmt(t)} L {fmt(r-R)},{fmt(t)} A {fmt(R)},{fmt(R)} 0 0 1 {fmt(r)},{fmt(t+R)} "
                f"L {fmt(r)},{fmt(b-R)} A {fmt(R)},{fmt(R)} 0 0 1 {fmt(r-R)},{fmt(b)} "
                f"L {fmt(l+R)},{fmt(b)} A {fmt(R)},{fmt(R)} 0 0 1 {fmt(l)},{fmt(b-R)} "
                f"L {fmt(l)},{fmt(t+R)} A {fmt(R)},{fmt(R)} 0 0 1 {fmt(l+R)},{fmt(t)} Z")
    return (f"M {fmt(l+R)},{fmt(t)} A {fmt(R)},{fmt(R)} 0 0 0 {fmt(l)},{fmt(t+R)} "
            f"L {fmt(l)},{fmt(b-R)} A {fmt(R)},{fmt(R)} 0 0 0 {fmt(l+R)},{fmt(b)} "
            f"L {fmt(r-R)},{fmt(b)} A {fmt(R)},{fmt(R)} 0 0 0 {fmt(r)},{fmt(b-R)} "
            f"L {fmt(r)},{fmt(t+R)} A {fmt(R)},{fmt(R)} 0 0 0 {fmt(r-R)},{fmt(t)} Z")


def ring(cx, cy, hw, hh, S, Ro, inner_factor=0.7):
    """A hollow rounded rectangle of border thickness S as ONE path (outer + reversed
    inner). Inner corner radius is kept generous (Apple does not use a strict
    concentric offset): Ri ~= Ro - inner_factor*S, so corners read rounded inside too."""
    Ri = max(0.4, Ro - inner_factor * S)
    return rrect(cx, cy, hw, hh, Ro, cw=True) + " " + rrect(cx, cy, hw - S, hh - S, Ri, cw=False)


def reflect_path(d, pivot):
    """Mirror a path vertically around y=pivot. Negates y AND flips each arc's sweep
    flag — required, or arcs bulge the wrong way (concave caps, broken holes).
    Handles the absolute M/L/A/Z output of the helpers above."""
    toks = re.findall(r"[MLAZ]|-?\d+\.?\d*", d)
    out, i = [], 0
    ry = lambda y: 2 * pivot - float(y)
    while i < len(toks):
        t = toks[i]
        if t in ("M", "L"):
            out.append(f"{t} {fmt(float(toks[i+1]))},{fmt(ry(toks[i+2]))}"); i += 3
        elif t == "A":
            rx, r2, rot, laf, sf, x, y = toks[i+1:i+8]
            out.append(f"A {rx},{r2} {rot} {laf} {'1' if sf=='0' else '0'} {fmt(float(x))},{fmt(ry(y))}"); i += 8
        elif t == "Z":
            out.append("Z"); i += 1
        else:
            i += 1
    return " ".join(out)


def bbox(paths):
    """Crude bbox from coordinate pairs. NOTE: arc radii/flags are not coordinate pairs
    and may slightly pollute extremes; prefer passing an explicit bbox you computed
    from your geometry. Use only as a fallback."""
    pts = re.findall(r"(-?\d+\.?\d*),(-?\d+\.?\d*)", " ".join(paths))
    xs = [float(a) for a, _ in pts]; ys = [float(b) for _, b in pts]
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------- preview
def preview_svg(paths, box, scale=4):
    """Standalone, transparent, black-filled SVG of just the glyph (for rasterizing)."""
    x0, y0, x1, y1 = box
    pad = 4
    vb = (x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
    body = "\n".join(f'<path fill="black" fill-rule="nonzero" d="{p}"/>' for p in paths)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(vb[0])} {fmt(vb[1])} '
            f'{fmt(vb[2])} {fmt(vb[3])}" width="{int(vb[2]*scale)}" height="{int(vb[3]*scale)}">\n'
            f"{body}\n</svg>\n")


# ---------------------------------------------------------------- template
def _minimal_scaffold():
    """Self-contained Template v.4.0 scaffold (used when SF Symbols.app is absent).
    Has the ids assemble_template() edits: margin guides, Symbols, descriptive-name."""
    def txt(x, y, s, anchor="start", bold=False):
        b = "font-weight:bold;" if bold else ""
        a = f"text-anchor:{anchor};" if anchor != "start" else ""
        return (f'<text style="stroke:none;fill:black;font-family:sans-serif;font-size:13;{b}{a}" '
                f'transform="matrix(1 0 0 1 {x} {y})">{s}</text>')
    guides = []
    for sc, (cap, base) in {"S": (CAPLINE_S, BASELINE_S), "M": (1055.54, 1126.0), "L": (1485.54, 1556.0)}.items():
        guides.append(f'<line id="Capline-{sc}" style="fill:none;stroke:#27AAE1;stroke-width:0.5;" x1="263" x2="3036" y1="{cap}" y2="{cap}"/>')
        guides.append(f'<line id="Baseline-{sc}" style="fill:none;stroke:#27AAE1;stroke-width:0.5;" x1="263" x2="3036" y1="{base}" y2="{base}"/>')
    for w in WEIGHTS:
        c = COLCENTER[w]
        guides.append(f'<line id="left-margin-{w}-S" style="fill:none;stroke:#FF3B30;stroke-width:0.5;" x1="{c-40}" x2="{c-40}" y1="600" y2="720"/>')
        guides.append(f'<line id="right-margin-{w}-S" style="fill:none;stroke:#00AEEF;stroke-width:0.5;" x1="{c+40}" x2="{c+40}" y1="600" y2="720"/>')
    style = (".monochrome-0 {fill:#FFFFFF;opacity:0.0;-sfsymbols-clear-behind:true}\n"
             ".monochrome-1 {fill:#000000}\n"
             ".multicolor-0:tintColor {fill:#007AFF;opacity:0.0;-sfsymbols-clear-behind:true}\n"
             ".multicolor-1:tintColor {fill:#007AFF}\n"
             ".hierarchical-0:primary {fill:#212121;opacity:0.0;-sfsymbols-clear-behind:true}\n"
             ".hierarchical-1:primary {fill:#212121}\n"
             ".SFSymbolsPreview007AFF {fill:#007AFF;opacity:1.0}\n"
             ".SFSymbolsPreviewFFFFFF {fill:#FFFFFF;opacity:1.0}")
    notes = ("\n  ".join([
        '<rect height="2200" id="artboard" style="fill:white;opacity:1" width="3300" x="0" y="0"/>',
        txt(263, 726, "Small"), txt(263, 1156, "Medium"), txt(263, 1586, "Large"),
        '<text id="template-version" style="stroke:none;fill:black;font-family:sans-serif;font-size:13;text-anchor:end;" transform="matrix(1 0 0 1 3036 1933)">Template v.4.0</text>',
        '<text id="descriptive-name" style="stroke:none;fill:black;font-family:sans-serif;font-size:13;text-anchor:end;" transform="matrix(1 0 0 1 3036 1969)">custom.symbol</text>',
    ]))
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="3300" height="2200">\n'
            f' <style>{style}\n </style>\n'
            f' <g id="Notes">\n  {notes}\n </g>\n'
            f' <g id="Guides">\n  ' + "\n  ".join(guides) + "\n </g>\n"
            f' <g id="Symbols">\n </g>\n</svg>\n')


def assemble_template(name, weight_paths, scaffold_path=None):
    """Build a Template v.4.0 SVG string.

    weight_paths: {"Ultralight": (paths, box), "Regular": (...), "Black": (...)}
      paths = list of path 'd' strings in design space (y-down, x centered on 0)
      box   = (x0, y0, x1, y1) bbox of the ink in design space

    Each weight is centered on its column and vertically centered on the cap band.
    """
    src = scaffold_path or SCAFFOLD_DEFAULT
    s = open(src).read() if os.path.exists(src) else _minimal_scaffold()
    margins, syms = {}, []
    for w in ["Black", "Regular", "Ultralight"]:
        paths, (x0, y0, x1, y1) = weight_paths[w]
        hw = (x1 - x0) / 2.0
        dc = (y0 + y1) / 2.0
        tx, ty = COLCENTER[w], CAPBAND - dc
        inner = "\n   ".join(f'<path class="{CLS}" d="{p}"/>' for p in paths)
        syms.append(f'  <g id="{w}-S" transform="matrix(1 0 0 1 {fmt(tx)} {fmt(ty)})">\n   {inner}\n  </g>')
        margins[w] = (tx - hw, tx + hw)

    def setline(text, lid, x):
        return re.sub(rf'(<line id="{lid}"[^>]*?x1=")[^"]*("[^>]*?x2=")[^"]*(")',
                      rf"\g<1>{fmt(x)}\g<2>{fmt(x)}\g<3>", text)

    for w in WEIGHTS:
        l, r = margins[w]
        s = setline(s, f"left-margin-{w}-S", l)
        s = setline(s, f"right-margin-{w}-S", r)
    s = re.sub(r'<g id="Symbols">.*?</g>\n</svg>',
               '<g id="Symbols">\n' + "\n".join(syms) + "\n </g>\n</svg>", s, flags=re.S)
    s = re.sub(r'(id="descriptive-name"[^>]*>)[^<]*(</text>)', rf"\g<1>{name}\g<2>", s)
    return s


def write_symbolset(out_dir, name, svg):
    """Write <out_dir>/<name>.symbolset/ (Contents.json + <name>.svg) and a top-level
    editable copy <out_dir>/<name>.svg. Returns the symbolset path."""
    ss = os.path.join(out_dir, f"{name}.symbolset")
    os.makedirs(ss, exist_ok=True)
    with open(os.path.join(out_dir, f"{name}.svg"), "w") as f:
        f.write(svg)
    with open(os.path.join(ss, f"{name}.svg"), "w") as f:
        f.write(svg)
    with open(os.path.join(ss, "Contents.json"), "w") as f:
        f.write('{\n  "info" : {\n    "author" : "xcode",\n    "version" : 1\n  },\n'
                '  "symbols" : [\n    {\n      "filename" : "' + name + '.svg",\n'
                '      "idiom" : "universal"\n    }\n  ]\n}\n')
    return ss
