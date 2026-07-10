"""Combine a folder of numbered PNG frames into a body.gif for a char pack.

Usage:
    python tools/make_gif.py <frames_dir> <output.gif> [--duration-ms 90]

<frames_dir> must contain PNGs that sort into the correct animation
order by filename (e.g. frame_00.png, frame_01.png, ...) and must all
share the exact same canvas size — mismatched sizes will shift your
eye-socket alignment, so this script refuses to proceed if it finds any.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames_dir", type=Path, help="Folder of frame_*.png files, in order")
    parser.add_argument("output_gif", type=Path, help="Where to write the combined GIF")
    parser.add_argument("--duration-ms", type=int, default=90, help="Milliseconds per frame")
    args = parser.parse_args()

    frame_paths = sorted(args.frames_dir.glob("*.png"))
    if not frame_paths:
        print(f"No PNG files found in {args.frames_dir}", file=sys.stderr)
        return 1

    frames = [Image.open(p).convert("RGBA") for p in frame_paths]

    sizes = {f.size for f in frames}
    if len(sizes) > 1:
        print(
            "ERROR: frames have mismatched canvas sizes: "
            + ", ".join(str(s) for s in sizes)
            + "\nAll frames must be the exact same size, or the eye-socket "
            "coordinates in config.json will no longer line up with the face.",
            file=sys.stderr,
        )
        return 1

    print(f"Combining {len(frames)} frames ({frames[0].size[0]}x{frames[0].size[1]}) "
          f"at {args.duration_ms}ms/frame -> {args.output_gif}")

    frames[0].save(
        args.output_gif,
        save_all=True,
        append_images=frames[1:],
        duration=args.duration_ms,
        loop=0,
        disposal=2,
    )
    print("Done. Point your char pack's config.json \"body\" field at this file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
