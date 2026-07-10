"""Auto-detect eye/pupil positions in a char pack image.

Only works when the art still has visible dark pupils (like a typical
reference image before you erase them for PixelPal's tracking pupil).
If your art has light-colored eyes, or you've already blanked the
pupils out, use tools/eye_picker.html instead — this script has
nothing dark to detect at that point.

Usage:
    pip install pillow numpy scipy
    python tools/find_eye_coords.py path/to/image.png
"""

from __future__ import annotations

import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def find_dark_blobs(image_path: str, max_blobs: int = 6):
    im = Image.open(image_path).convert("RGBA")
    arr = np.array(im)
    r, g, b, a = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int), arr[..., 3]

    dark = (r < 60) & (g < 60) & (b < 60) & (a > 200)

    labeled, n = ndimage.label(dark)
    if n == 0:
        print("No dark blobs found. If your art doesn't have near-black pupils "
              "(e.g. light-colored eyes, or already-erased sockets), use "
              "tools/eye_picker.html instead — click-based, works on any art.")
        return

    sizes = ndimage.sum(dark, labeled, range(1, n + 1))
    order = np.argsort(sizes)[::-1][:max_blobs]

    print(f"Image size: {im.size[0]} x {im.size[1]}\n")
    print(f"Top {len(order)} dark regions found (biggest first) — "
          "the two largest AWAY from image edges are usually your pupils:\n")

    for rank, idx in enumerate(order, start=1):
        comp_id = idx + 1
        size = sizes[idx]
        ys, xs = np.where(labeled == comp_id)
        cx, cy = xs.mean(), ys.mean()
        radius = ((xs.max() - xs.min()) + (ys.max() - ys.min())) / 4
        print(f"  #{rank}  center=({cx:.0f}, {cy:.0f})  approx radius={radius:.0f}px  pixel_count={size:.0f}")

    print(
        "\nOnce you've identified which two are your left/right pupils, "
        "paste into config.json (remember: erase the original pupils in your "
        "image editor first, since PixelPal draws its own moving pupil on top):\n"
    )
    print('  "eyes": {')
    print('    "left":  { "x": <copy x>, "y": <copy y>, "radius": <copy radius minus a few px>, "damping": 0.15 },')
    print('    "right": { "x": <copy x>, "y": <copy y>, "radius": <copy radius minus a few px>, "damping": 0.15 },')
    print('    "pupil": "pupil.png"')
    print('  }')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/find_eye_coords.py path/to/image.png")
        sys.exit(1)
    find_dark_blobs(sys.argv[1])
