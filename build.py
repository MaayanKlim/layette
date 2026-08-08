#!/usr/bin/env python3
"""
Wrap src.html (a headless fragment) into a complete standalone index.html
for GitHub Pages, and generate the home-screen icon.

src.html stays headless so the same file can also be published as a Claude
artifact, where the platform supplies its own <head>. On a real host nothing
supplies one, so the viewport tag has to be added here or mobile browsers
fall back to a 980px desktop layout.
"""

import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).parent
GROUND_LIGHT = "#F4F6F9"
GROUND_DARK = "#0E1116"
INDIGO = (0x2F, 0x4B, 0x8F)
CREAM = (0xF4, 0xF6, 0xF9)


def build_html() -> None:
    src = (ROOT / "src.html").read_text(encoding="utf-8")

    split_at = src.index('<div class="wrap">')
    head_src, body = src[:split_at], src[split_at:]

    title = re.search(r"<title>(.*?)</title>", head_src, re.S).group(1).strip()
    # Keep the boot script and stylesheet, drop the bare <title> we just parsed.
    head_src = re.sub(r"<title>.*?</title>\s*", "", head_src, count=1, flags=re.S).strip()

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Newborn clothes inventory tracker with per-size targets and remaining cost.">
<meta name="color-scheme" content="light dark">
<meta id="themeColor" name="theme-color" content="{GROUND_LIGHT}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{title}">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="icon.png">
<link rel="icon" type="image/png" href="icon.png">
{head_src}
</head>
<body>
{body.rstrip()}
</body>
</html>
"""
    (ROOT / "index.html").write_text(doc, encoding="utf-8")
    print(f"index.html written ({len(doc):,} bytes)")


def build_icon(size: int = 180) -> None:
    """Solid indigo tile with three stacked bars, drawn without any image library."""
    px = [[INDIGO] * size for _ in range(size)]

    def rounded_bar(x0, y0, x1, y1, radius):
        for y in range(y0, y1):
            for x in range(x0, x1):
                # Round the corners by testing distance from each corner centre.
                cx = None
                if x < x0 + radius and y < y0 + radius:
                    cx, cy = x0 + radius, y0 + radius
                elif x >= x1 - radius and y < y0 + radius:
                    cx, cy = x1 - radius - 1, y0 + radius
                elif x < x0 + radius and y >= y1 - radius:
                    cx, cy = x0 + radius, y1 - radius - 1
                elif x >= x1 - radius and y >= y1 - radius:
                    cx, cy = x1 - radius - 1, y1 - radius - 1
                if cx is not None and (x - cx) ** 2 + (y - cy) ** 2 > radius ** 2:
                    continue
                px[y][x] = CREAM

    # Three folded stacks, narrowing toward the top for a sense of a pile.
    for i, (inset, top) in enumerate(((22, 116), (32, 76), (42, 36))):
        rounded_bar(inset, top, size - inset, top + 28, 9)

    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in px)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    (ROOT / "icon.png").write_bytes(png)
    print(f"icon.png written ({len(png):,} bytes, {size}x{size})")


if __name__ == "__main__":
    build_html()
    build_icon()
