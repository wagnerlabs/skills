// svg2png.swift — rasterize an SVG to PNG using the system renderer (NSImage), PRESERVING
// aspect ratio. Used to preview the custom glyph and compare it to references.
//
// Build: swiftc -O svg2png.swift -o svg2png
// Use:   ./svg2png <in.svg> <out.png> <longSidePx>
//
// CRITICAL: it scales so the LONGER side == longSidePx and keeps the other side
// proportional. Do NOT render into a fixed square — a taller-than-wide glyph would get
// stretched horizontally and look wrong (this is a real bug that fooled an earlier pass).
//
// Requires macOS 13+ (NSImage SVG support).

import AppKit
import Foundation

let a = CommandLine.arguments
guard a.count >= 4 else { FileHandle.standardError.write("usage: in.svg out.png longSidePx\n".data(using:.utf8)!); exit(1) }
let inp = a[1], out = a[2]
let longSide = CGFloat(Double(a[3]) ?? 512)

guard let data = try? Data(contentsOf: URL(fileURLWithPath: inp)),
      let img = NSImage(data: data) else {
    FileHandle.standardError.write("could not load SVG: \(inp)\n".data(using:.utf8)!); exit(2)
}
let isz = img.size
guard isz.width > 0, isz.height > 0 else { FileHandle.standardError.write("zero-size SVG\n".data(using:.utf8)!); exit(3) }
let s = longSide / max(isz.width, isz.height)          // preserve aspect ratio
let W = Int((isz.width * s).rounded()), H = Int((isz.height * s).rounded())
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: W, pixelsHigh: H,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSGraphicsContext.current?.imageInterpolation = .high
img.draw(in: NSRect(x: 0, y: 0, width: W, height: H))
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
print("ok \(isz) -> \(W)x\(H)")
