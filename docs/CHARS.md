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
    "happy": "expressions/happy.png",
    "worried": "expressions/worried.png",
    "sleepy": "expressions/sleepy.png"
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
| `expressions.<mood>`        |          | Overlay sprite shown when the mood state machine enters `<mood>`. Valid keys: `idle`, `alert`, `sleepy`, `happy`, `worried`, `excited`. Any mood without an entry simply shows no overlay. |

## Coordinate space

All coordinates (`eyes.*.x/y`, `head_tilt.pivot`) are in the **same pixel
space as your body sprite**, with `(0, 0)` at the top-left. If your body
image is 96×96px, an eye at `x: 36, y: 46` sits 36px from the left edge and
46px down.

## Animated bodies

If `body` ends in `.gif`, PixelPal treats it as an idle-cycle animation: it
holds on frame 0, plays the GIF through exactly once every `wait_seconds`,
then returns to holding frame 0 — rather than looping continuously. This
keeps a "breathing"/tail-flick feel instead of a busy-looking video clip.
Static `.png` bodies just render as-is with no cycling.

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
