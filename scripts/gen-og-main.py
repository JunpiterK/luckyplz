#!/usr/bin/env python3
"""Export the site sharing card and the PNG used by previously shared links."""
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ARTWORK = ROOT / "scripts" / "og-assets" / "lucky-please-game-night.webp"
ASSETS = ROOT / "public" / "assets"
CARD_SIZE = (1200, 630)


def main():
    with Image.open(ARTWORK) as source:
        card = ImageOps.fit(source.convert("RGB"), CARD_SIZE, method=Image.Resampling.LANCZOS)

    jpeg = ASSETS / "lucky-please-game-night.jpg"
    card.save(jpeg, quality=89, optimize=True)
    # Old messages can still request the original URL with its cached query string.
    legacy = ASSETS / "og-image.png"
    card.quantize(colors=256).save(legacy, optimize=True)

    for path in (jpeg, legacy):
        print(f"{path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
