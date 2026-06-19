// render_reference.swift — render a real (Apple) SF Symbol to a black-on-transparent PNG,
// so you can MEASURE its native stroke weight / corner radii / proportions and match them.
//
// Build: swiftc -O render_reference.swift -o render_reference
// Use:   ./render_reference <symbol.name> <weight> <pointSize> <out.png>
//        ./render_reference arrow.up regular 400 arrow.up_regular.png
// Weights: ultralight thin light regular medium semibold bold heavy black
//
// Tip: render at 4x the template size (e.g. 400 for a 100pt template) so 1 template unit
// = 4 px; divide measured pixels by 4 to get template units.

import AppKit
import Foundation

let a = CommandLine.arguments
guard a.count >= 5 else { FileHandle.standardError.write("usage: name weight pointSize out.png\n".data(using:.utf8)!); exit(1) }
let name = a[1], wStr = a[2].lowercased()
let size = CGFloat(Double(a[3]) ?? 256)
let out = a[4]

let weights: [String: NSFont.Weight] = [
    "ultralight": .ultraLight, "thin": .thin, "light": .light, "regular": .regular,
    "medium": .medium, "semibold": .semibold, "bold": .bold, "heavy": .heavy, "black": .black,
]
let cfg = NSImage.SymbolConfiguration(pointSize: size, weight: weights[wStr] ?? .regular)
guard let base = NSImage(systemSymbolName: name, accessibilityDescription: nil),
      let img = base.withSymbolConfiguration(cfg) else {
    FileHandle.standardError.write("no such symbol: \(name)\n".data(using:.utf8)!); exit(2)
}
let W = Int(img.size.width.rounded()), H = Int(img.size.height.rounded())
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: W, pixelsHigh: H,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSColor.black.set()
let r = NSRect(x: 0, y: 0, width: img.size.width, height: img.size.height)
img.draw(in: r)
r.fill(using: .sourceAtop)               // force solid black template ink
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
print("\(name) \(wStr): \(W)x\(H)")
