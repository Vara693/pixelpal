"""One-off generator for placeholder char-pack art (not part of the shipped package).

Produces small, clearly-placeholder sprites (flat shapes, no attempt at
polish) good enough to prove the rendering engine works end-to-end.
Real char packs should replace these with real art — see docs/CHARS.md.
"""

import math
import os

from PIL import Image, ImageDraw

CANVAS = 96
OUT_ROOT = os.path.join(os.path.dirname(__file__), "..", "chars")


def _new():
    return Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))


def make_body_frames(base_color, ear_shape, n_frames=8):
    """Simple idle 'breathing' + ear/tail flick cycle."""
    frames = []
    for i in range(n_frames):
        img = _new()
        d = ImageDraw.Draw(img)
        t = i / n_frames
        breathe = math.sin(t * 2 * math.pi) * 2

        # body (rounded head/torso blob)
        body_top = 30 - breathe
        d.ellipse([14, body_top, 82, 90], fill=base_color, outline=(0, 0, 0, 180), width=2)

        # ears, animal-specific shape callback draws + a slight twitch angle
        twitch = math.sin(t * 2 * math.pi + 1.0) * 6
        ear_shape(d, twitch, base_color)

        # simple static muzzle/nose so it doesn't look like a blank disc
        d.ellipse([44, 54, 52, 60], fill=(0, 0, 0, 160))

        frames.append(img)
    return frames


def ears_cat(d, twitch, color):
    d.polygon([(22, 34), (30 + twitch * 0.3, 8), (40, 30)], fill=color, outline=(0, 0, 0, 180))
    d.polygon([(74, 34), (66 - twitch * 0.3, 8), (56, 30)], fill=color, outline=(0, 0, 0, 180))


def ears_fox(d, twitch, color):
    d.polygon([(20, 36), (28 + twitch * 0.4, 4), (42, 32)], fill=color, outline=(0, 0, 0, 180))
    d.polygon([(76, 36), (68 - twitch * 0.4, 4), (54, 32)], fill=color, outline=(0, 0, 0, 180))
    d.polygon([(28, 30), (30, 14), (36, 28)], fill=(255, 255, 255, 255))
    d.polygon([(68, 30), (66, 14), (60, 28)], fill=(255, 255, 255, 255))


def ears_owl(d, twitch, color):
    # owls: little "ear tuft" feathers instead of cat/fox-style ears
    d.polygon([(30, 26), (26 + twitch * 0.2, 14), (36, 24)], fill=color, outline=(0, 0, 0, 180))
    d.polygon([(66, 26), (70 - twitch * 0.2, 14), (60, 24)], fill=color, outline=(0, 0, 0, 180))


def save_gif(frames, path, duration_ms=90):
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )


def make_pupil(path, radius=5, color=(20, 20, 20, 255)):
    size = radius * 2 + 2
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, size - 2, size - 2], fill=color)
    img.save(path)


def make_closed_eye(path, width=16, height=8):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.arc([0, -height, width, height], start=20, end=160, fill=(20, 20, 20, 255), width=2)
    img.save(path)


def make_expression(path, kind, width=28, height=14):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == "happy":
        d.arc([2, -6, width - 2, height + 2], start=10, end=170, fill=(30, 20, 10, 255), width=3)
    elif kind == "worried":
        d.arc([2, height - 6, width - 2, height + 14], start=200, end=340, fill=(30, 20, 10, 255), width=3)
        d.line([(6, 2), (12, 6)], fill=(30, 20, 10, 255), width=2)
        d.line([(width - 6, 2), (width - 12, 6)], fill=(30, 20, 10, 255), width=2)
    elif kind == "sleepy":
        d.line([(4, height // 2), (width - 4, height // 2)], fill=(30, 20, 10, 255), width=2)
    elif kind == "alert":
        d.line([(4, 2), (11, 0)], fill=(30, 20, 10, 255), width=2)
        d.line([(width - 4, 2), (width - 11, 0)], fill=(30, 20, 10, 255), width=2)
        d.ellipse([width / 2 - 4, height - 10, width / 2 + 4, height - 2], outline=(30, 20, 10, 255), width=2)
    elif kind == "excited":
        d.pieslice([2, -8, width - 2, height + 6], start=10, end=170, fill=(30, 20, 10, 255))
        d.pieslice([5, -8, width - 5, height], start=10, end=170, fill=(255, 255, 255, 255))
    img.save(path)


def build_character(name, base_color, ear_shape_fn):
    out_dir = os.path.join(OUT_ROOT, name)
    os.makedirs(os.path.join(out_dir, "expressions"), exist_ok=True)

    frames = make_body_frames(base_color, ear_shape_fn)
    save_gif(frames, os.path.join(out_dir, "body.gif"))

    make_pupil(os.path.join(out_dir, "pupil.png"))
    make_closed_eye(os.path.join(out_dir, "eye_closed.png"))

    for mood in ("happy", "worried", "sleepy", "alert", "excited"):
        make_expression(os.path.join(out_dir, "expressions", f"{mood}.png"), mood)


if __name__ == "__main__":
    build_character("cat", (235, 150, 60, 255), ears_cat)
    build_character("fox", (230, 110, 40, 255), ears_fox)
    build_character("owl", (140, 110, 90, 255), ears_owl)
    print("Generated placeholder art for cat, fox, owl.")
