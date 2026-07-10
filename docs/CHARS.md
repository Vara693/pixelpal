# Authoring a character pack

A character pack is a folder (or a `.zip` of one) containing a `config.json`
plus the art it references. The rendering engine (`pixelpal/rendering/`) is
completely generic — it never hardcodes "cat" or "fox", it only reads
geometry and asset paths from your `config.json`. If your pack validates
against the schema below, it works.

## Minimum viable pack

```
my_pack/
├── config.json
├── body.png          (or body.gif)
└── pupil.png
```

```json
{
  "name": "my_pack",
  "body": "body.png",
  "eyes": {
    "left":  { "x": 34, "y": 28, "radius": 4 },
    "right": { "x": 58, "y": 28, "radius": 4 },
    "pupil": "pupil.png"
  }
}
```

That's a fully valid pack — `name`, `body`, and `eyes` are the only required
fields. Everything below is optional.

## Full schema

```json
{
  "name": "fox",
  "display_name": "Fox",
  "body": "body.gif",
  "wait_seconds": 5,
  "eyes": {
    "left":  { "x": 34, "y": 28, "radius": 4, "damping": 0.15 },
    "right": { "x": 58, "y": 28, "radius": 4, "damping": 0.15 },
    "pupil": "pupil.png",
    "closed": "eye_closed.png"
  },
  "head_tilt": {
    "enabled": true,
    "max_degrees": 6,
    "pivot": { "x": 46, "y": 40 }
  },
  "ears": {
    "enabled": false
  },
  "expressions": {
    "happy": { "path": "expressions/happy.png", "x": 46, "y": 55 },
    "worried": { "path": "expressions/worried.png", "x": 46, "y": 55 },
    "alert": { "path": "expressions/alert.png", "x": 46, "y": 55 },
    "excited": { "path": "expressions/excited.png", "x": 46, "y": 55 },
    "sleepy": { "path": "expressions/sleepy.png", "x": 46, "y": 55 }
  }
}
```

### Field reference

| Field                    | Required | Notes                                                                 |
|---------------------------|----------|------------------------------------------------------------------------|
| `name`                    | ✅       | Unique identifier; must match the folder name it's installed under.    |
| `display_name`            |          | Shown in the right-click menu. Defaults to `name.title()`.             |
| `body`                    | ✅       | Relative path to a `.png` (static) or `.gif` (animated) body sprite.   |
| `wait_seconds`            |          | Idle hold time before the body animation plays once. Default `5`.      |
| `eyes.left` / `eyes.right`| ✅       | Socket center (`x`,`y`), `radius` the pupil can travel within, `damping` (0-1, default `0.15`; lower = smoother/slower). |
| `eyes.pupil`               | ✅       | Pupil sprite, drawn centered on the computed position.                 |
| `eyes.closed`              |          | Sprite shown instead of the pupil when the pet is `sleepy`.            |
| `head_tilt.enabled`        |          | Whole-body rotation toward the cursor. Default `false`.                 |
| `head_tilt.max_degrees`    |          | Rotation clamp. Default `6`.                                            |
| `head_tilt.pivot`          |          | Rotation pivot point, in the same coordinate space as the eye sockets. |
| `ears.enabled`              |          | Enables the sound-reactive ear twitch (also needs `[ears] audio_reactive = true` in the user's config.ini). |
| `expressions.<mood>`        |          | Overlay shown when the mood state machine enters `<mood>`. Object with `path`, `x`, `y` — `x`/`y` are where the overlay's **center** is drawn, in the same coordinate space as the eyes (usually the mouth). Valid keys: `idle`, `alert`, `sleepy`, `happy`, `worried`, `excited`. Any mood without an entry simply shows no overlay. A bare string (`"happy": "expressions/happy.png"`) is still accepted as shorthand for `{"path": ..., "x": 0, "y": 0}`, but that anchors it to the window's top-left corner — almost never what you want, so always specify `x`/`y` explicitly. |

## Coordinate space

All coordinates (`eyes.*.x/y`, `head_tilt.pivot`, `expressions.*.x/y`) are in
the **same pixel space as your body sprite**, with `(0, 0)` at the top-left.
If your body image is 96×96px, an eye at `x: 36, y: 46` sits 36px from the
left edge and 46px down.

### Finding those coordinates

Two tools in `tools/` help you get exact numbers instead of guessing:

- **`tools/eye_picker.html`** — open it directly in a browser (no install
  needed), drag your image in, click on each point you need (left eye,
  right eye, mouth, head-tilt pivot), and it prints ready-to-paste
  `{"x": ..., "y": ...}` JSON. Works on any art style, including ones with
  no visible pupils yet.
- **`tools/find_eye_coords.py`** — for art that *already* has visible dark
  pupils (e.g. a reference image before you've adapted it for PixelPal),
  this auto-detects them:
  ```bash
  python tools/find_eye_coords.py path/to/reference.png
  ```
  It ranks dark regions by size — usually your two pupils are the two
  largest, away from the image edges.

### Adapting art that already has drawn-on eyes

If your reference art has pupils baked into the image (most stock/AI-
generated character art does), you need to erase them before using it as
`body` — otherwise you'll get two pupils: the static drawn one plus
PixelPal's moving one on top. The general process:

1. Find the pupil coordinates (`find_eye_coords.py` above).
2. In an image editor (or a script, using the pupil coordinates as a
   guide), fill the pupil area with the surrounding eye-white/sclera
   color so the sockets read as blank.
3. Create a small standalone `pupil.png` matching your art's original
   pupil style (color, any highlight/glint) — this is what PixelPal
   actually animates.
4. Set `eyes.*.radius` conservatively: smaller than the visible white
   area minus your new pupil's own radius, so it never visibly pokes
   past the eye outline while tracking the cursor.

## Animated bodies

If `body` ends in `.gif`, PixelPal treats it as an idle-cycle animation: it
holds on frame 0, plays the GIF through exactly once every `wait_seconds`,
then returns to holding frame 0 — rather than looping continuously. This
keeps a "breathing"/tail-flick feel instead of a busy-looking video clip.
Static `.png` bodies just render as-is with no cycling.

**Important constraint:** eye/expression coordinates in `config.json` are
fixed pixel positions. If your GIF's frames shift, tilt, or resize the
head/eye area, the pupils won't follow — they'll drift out of alignment
because they don't know the face moved. Safe to animate across frames:
tail wag, chest/belly bounce, ear twitch. Unsafe: anything that moves the
eye region itself.

### Building a GIF from frames

Export each frame as a same-size, transparent-background PNG
(`frame_00.png`, `frame_01.png`, ...), then combine them:

```bash
python tools/make_gif.py path/to/frames_dir/ chars/my_pack/body.gif --duration-ms 90
```

This refuses to run if your frames aren't all identical dimensions —
mismatched sizes are exactly the kind of mistake that throws off eye
alignment, so it's caught before it ships.

## Validating your pack

```python
from pixelpal.charpack.loader import load_char_pack
pack = load_char_pack("path/to/my_pack")   # raises CharPackLoadError with details on failure
```

Or just try installing it via the right-click menu → **Install char pack...**
— validation errors are shown in a dialog before anything is copied into
place.

## Packaging as a zip

Zip the folder itself (or its *contents* directly at the zip root — both
layouts are accepted):

```bash
cd chars/
zip -r my_pack.zip my_pack/
```

The installer (`pixelpal/charpack/installer.py`) validates the pack fully
before copying it into your local `chars/` directory, and refuses to
overwrite an already-installed pack with the same `name`.
