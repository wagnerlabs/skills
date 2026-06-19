---
name: custom-sf-symbols
description: >-
  Create custom SF Symbols (macOS/iOS) that look native. Measure real Apple symbols for
  authentic stroke weights and corner radii, build parametric SVG paths across the
  Ultralight/Regular/Black weights in Apple's "Template v.4.0" format, verify with
  aspect-correct previews, and package as a .symbolset. Use when asked to design a new SF
  Symbol or custom glyph, match the SF Symbols visual style, make a drop-in symbol for a
  button, or produce a variant/mirror of an existing system symbol.
---

# Creating custom SF Symbols

Custom SF Symbols are SVGs in Apple's annotated "Template v.4.0" format. A symbol that
"looks native" must match SF Symbols' optical metrics (stroke weight, corner radii, round
caps) and ship three key weights so the system can interpolate the rest. This skill builds
them by **measuring real Apple symbols** and reconstructing the shapes parametrically as
**filled outlines** (never stroked paths).

## When to use

- "Create / design an SF Symbol for X", "make a custom glyph that looks like a native SF
  Symbol", "a symbol matching `rectangle.grid.1x2`'s style", "a button icon in SF style".
- "Make a variant of `<symbol>`" — mirrored, restyled, or with proportions changed.
- The user provides a sketch/image and wants it as a native-looking symbol.

Not for: using existing Apple symbols (just reference them by name), or non-Apple icon sets.

## Prerequisites

- macOS (the rasterizers use AppKit; SVG loading needs macOS 13+).
- `swiftc` (Xcode or Command Line Tools).
- `python3` with Pillow: `python3 -m pip install --user Pillow`.
- **SF Symbols.app** (free from Apple) — strongly recommended. It is the source of the
  template scaffold and the only true validator/preview of the final symbol. If it is
  absent, the library falls back to a self-contained scaffold (generation still works;
  validate later in the app).

## Files in this skill

```
scripts/
  sfsymbol_lib.py        # capsule(), rrect(), ring(), reflect_path(), assemble_template(), write_symbolset()
  render_reference.swift # render a real SF Symbol to PNG for measuring
  svg2png.swift          # aspect-correct SVG -> PNG preview rasterizer
  measure.py             # measure stroke / dimensions / corner radius from a PNG
  example_build.py       # full worked example (copy + edit build_weight())
```

Compile the Swift tools once (binaries are NOT portable — recompile per machine):

```sh
cd scripts
swiftc -O render_reference.swift -o render_reference
swiftc -O svg2png.swift -o svg2png
```

## Step-by-step

Work in a scratch directory; keep `scripts/` on `PYTHONPATH` (run from `scripts/`, or
`export PYTHONPATH=…/scripts`).

1. **Pin the design.** Identify the component shapes (bars, rounded rectangles, arrows,
   chevrons) and, crucially, **which existing system symbol to match** for style (e.g.
   `rectangle`, `arrow.up`, `rectangle.grid.1x2`, `arrow.up.to.line`). If the user gave an
   image, decompose it into those primitives. If unsure of the impact/intent, ask.

2. **Render references** for the closest system symbol(s) at three weights, at 4× the
   template (use pointSize 400 so 1 template unit = 4 px):

   ```sh
   for w in ultralight regular black; do
     ./render_reference rectangle "$w" 400 ref_rectangle_$w.png
   done
   ```

3. **Measure** them and normalize to template units (divide px by 4):

   ```sh
   python3 measure.py ref_rectangle_regular.png --scale 4
   ```

   Capture: stroke width, outer corner radius, overall width/height, gaps. Typical Regular
   values: stroke ≈ 8, cap height = 70.459. Stroke roughly scales Ultralight ≈ 2.4,
   Regular ≈ 8, Black ≈ 17–19 (read the real numbers — they vary per symbol).

4. **Model the glyph parametrically** in `sfsymbol_lib` primitives, in design space
   (y-DOWN, x centered on 0), as filled outlines:
   - `capsule(p0, p1, r)` — bars, arrow shafts, chevron arms (round-capped thick segments).
   - `ring(cx, cy, hw, hh, S, Ro)` — a hollow rounded rectangle (border = S). Inner radius
     is auto-kept generous (`Ro - 0.7·S`) so inner corners read rounded too.
   - Compose by emitting several sibling paths (they union visually); give each weight one
     `(paths, bbox)` pair. Provide an EXPLICIT bbox from your math (don't trust `bbox()`).

5. **Vary only the stroke across weights.** Keep centerlines / outer dimensions the same;
   set S per weight from the measurements. This yields clean interpolation.

6. **Assemble + package:**

   ```python
   import sfsymbol_lib as sf
   weight_paths = {w: build_weight(w) for w in sf.WEIGHTS}      # build_weight -> (paths, bbox)
   svg = sf.assemble_template("my.symbol.name", weight_paths)   # centers on cap band, sets margins
   sf.write_symbolset("out", "my.symbol.name", svg)             # out/my.symbol.name.symbolset + .svg
   ```

7. **Preview aspect-correct and iterate.** Write standalone previews and rasterize:

   ```sh
   ./svg2png out/preview_Regular.svg out/preview_Regular.png 480
   ```

   Compare against the reference render or the user's image (overlay or side-by-side).
   Adjust radii/strokes/spacing and repeat until it reads native at small sizes too
   (re-render at ~24 px to check legibility).

8. **Validate** the template XML and confirm the symbolset copy matches:

   ```sh
   python3 -c "import xml.dom.minidom as m; m.parse('out/my.symbol.name.svg'); print('XML OK')"
   ```

   If SF Symbols.app is available, open the `.svg` (File ▸ Open) — it renders all nine
   weights × three scales and reports validation errors. This is the authoritative check.

9. **Deliver** the `.svg` (editable template) + `.symbolset` (drop into `.xcassets`) and
   show the user a preview image.

## Conventions and key numbers

- **Canvas** 3300 × 2200. **Small row:** baseline y = 696, capline y = 625.541 → cap height
  70.459. Glyphs are centered vertically on the cap band (y = 660.77) by `assemble_template`.
- **Key weights provided:** Ultralight, Regular, Black, all at the **Small** scale only; the
  system interpolates Thin…Heavy and Medium/Large.
- **Normalization:** rendered at pointSize 400 ⇒ divide measured px by 4 for template units.
- **Inner corner radius** of a stroked rounded rect ≈ `outerR − 0.7·stroke` (Apple does NOT
  use a strict concentric `outerR − stroke`; that collapses inner corners to near-square).
- **Naming:** lowercase, dot-separated (`anchor.top`, `proportional.sizing`). Custom names
  are free identifiers — reference via `Image("name")` / `NSImage(named:)` / `UIImage(named:)`,
  NOT `systemSymbolName:` (that only resolves Apple's built-ins).
- **Paths are FILLED outlines**, never `stroke=`. Holes use one path with outer + reversed
  inner winding (`ring()` does this).

## Expected output

```
<out>/
  <name>.svg                       # editable Template v.4.0 (open in SF Symbols.app)
  <name>.symbolset/
    Contents.json                  # {"info":{author:xcode,version:1},"symbols":[{filename,idiom:universal}]}
    <name>.svg
  preview_<Weight>.svg / .png      # verification previews (not shipped)
```

The template's `Symbols` group contains exactly three groups: `Ultralight-S`, `Regular-S`,
`Black-S`, each a `<g transform="matrix(1 0 0 1 tx ty)">` of `<path class="monochrome-1 …">`.

## Edge cases and failure modes

- **Preview stretched / wrong aspect (the #1 trap):** never rasterize into a fixed square.
  `svg2png.swift` scales the long side and keeps aspect. A square render silently widens a
  taller-than-wide glyph and makes correct geometry look stretched.
- **Square inner corners on a rounded rect:** caused by `innerR = outerR − stroke`. Use
  `ring()` (keeps `innerR ≈ outerR − 0.7·stroke`).
- **Heavy (Black) weight closes a hole into a solid blob:** a thick stroke needs a minimum
  cell height (`2·stroke + a few units`) to keep an opening. Clamp small cells at heavy
  weights — the ratio compresses slightly at Black; that is expected and interpolates fine.
  (See `MIN_HOLE` in `example_build.py`.)
- **Mirroring/flipping a glyph:** reflect with `reflect_path(d, pivot)` which negates y AND
  flips each arc sweep flag. Reflecting coordinates without flipping sweep produces concave
  caps and inverted holes. (Equivalently, just swap which cell/shape is where, avoiding arcs.)
- **Capsule caps bulging inward:** wrong arc sweep flag; `capsule()` is already correct —
  if you hand-write arcs, verify caps are convex by rendering.
- **Symbol won't import / validate:** ensure the `Symbols` group ids are exactly
  `Ultralight-S` / `Regular-S` / `Black-S`, guides + margin lines are present, and the SVG
  is well-formed. Prefer the SF Symbols.app scaffold (set `SF_SCAFFOLD` env var to a
  specific template if needed); fall back to the built-in scaffold otherwise.
- **Consumption surfaces differ:** native AppKit/UIKit/SwiftUI load custom symbols via
  `named:`. Cross-platform UI toolkits that draw SF Symbols from a bundled font (not asset
  catalogs) cannot use a `.symbolset` directly — render the SVG or add a font glyph instead.

## Test prompts

1. "Create a custom SF Symbol that looks native: a rounded rectangle with a horizontal bar
   above it and an up-arrow below pointing at the box. Give me the `.symbolset` and a preview."
2. "Make a symbol matching the style of `rectangle.grid.1x2`, but the top cell taller and the
   bottom cell shorter, keeping the same overall height. Then make a variant with the small
   cell on top."
3. "Here's a sketch [image]. Turn it into a native-looking SF Symbol in Ultralight/Regular/
   Black and show it next to the closest real system symbol so I can judge the match."
