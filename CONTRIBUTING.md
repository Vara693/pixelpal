# Contributing to PixelPal

Thanks for considering a contribution! A few ground rules to keep the
codebase easy to reason about.

## Project philosophy

- **`rendering/` stays generic.** No code in `pixelpal/rendering/` should
  ever reference a specific animal or character by name. If you're tempted
  to add a special case for "cat", it belongs in a char pack's
  `config.json` instead — see `docs/CHARS.md`.
- **Pure logic stays testable.** Math and state-transition logic (see
  `utils/geometry.py`, `mood/state_machine.py`, `charpack/schema.py`) is
  kept free of Qt/OS dependencies specifically so it can be unit tested
  without a display. New pure-logic code should follow the same pattern:
  plain functions/dataclasses in, plain values out.
- **Optional features stay optional and off by default.** Git watching,
  audio-reactive ears, and multi-pet awareness must not add overhead or
  behavior changes unless a user explicitly opts in.
- **No real keystroke/content logging, ever.** `activity_tracker.py` only
  ever produces aggregate counts. Any PR that makes it record *what* was
  typed/clicked, rather than just *that* something happened, will be
  rejected — see the Privacy stance section of the README.

## Getting set up

```bash
git clone <your fork>
cd pixelpal
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Adding a new mood signal

See `docs/MOOD_SYSTEM.md#writing-a-new-signal`. You should not need to
modify `state_machine.py` for a typical new signal — if you find yourself
doing so, that's a signal (no pun intended) the abstraction needs
revisiting; open an issue to discuss first.

## Adding a new character pack

Bundled packs live in `chars/`. Please include placeholder or
freely-licensed art only — see `docs/CHARS.md` for the schema and asset
requirements. PRs adding a new bundled character should include at least
the required `body`/`eyes` assets; `head_tilt`/`ears`/`expressions` are a
nice-to-have but not mandatory.

## Tests

- Pure-logic changes (geometry, mood transitions, schema validation, config
  persistence) need unit test coverage in `tests/`.
- Qt-dependent code (rendering widgets, the overlay window) is exercised
  manually per the phase-by-phase build order in `BUILD_PROMPT.md`; if you
  add meaningful non-Qt logic inside a Qt class, consider extracting it to
  a plain function so it can be tested directly.

## Code style

- Type hints on public functions/methods.
- Prefer explicit, small functions over clever one-liners.
- Run `pytest` before opening a PR; there's no separate linter configured
  yet — keep contributions PEP 8-reasonable.

## Reporting issues

Please include your OS, Python version, and (if relevant) whether you're on
X11, Wayland, macOS, or Windows — window-manager behavior is the single
biggest source of platform-specific bugs in this project.
