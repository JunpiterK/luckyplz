#!/usr/bin/env python3
"""Export the site sharing card, including images referenced by older previews."""
from pathlib import Path
from shutil import copyfile

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ARTWORK = ROOT / "scripts" / "og-assets" / "lucky-please-game-night.webp"
ASSETS = ROOT / "public" / "assets"
CARD_SIZE = (1200, 630)


def main():
    with Image.open(ARTWORK) as source:
        card = ImageOps.fit(source.convert("RGB"), CARD_SIZE, method=Image.Resampling.LANCZOS)

    jpeg = ASSETS / "lucky-please-game-night-v2.jpg"
    card.save(jpeg, quality=89, optimize=True)
    # A messenger can retain an old image URL after the page metadata changes.
    previous_jpeg = ASSETS / "lucky-please-game-night.jpg"
    copyfile(jpeg, previous_jpeg)
    legacy = ASSETS / "og-image.png"
    card.quantize(colors=256).save(legacy, optimize=True)

    for path in (jpeg, previous_jpeg, legacy):
        print(f"{path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
