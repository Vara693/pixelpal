# Mood system reference

PixelPal's mood is a small state machine (`pixelpal/mood/state_machine.py`)
driven entirely by pluggable **signal sources** (`pixelpal/mood/signals/`).
The state machine has zero knowledge of *how* any signal detects things —
it only reacts to the `MoodEvent` values a signal's `poll()` returns. This
is what lets new signals get added without touching `state_machine.py`.

## States

| State      | Kind       | Cleared by                                  |
|------------|------------|-----------------------------------------------|
| `idle`     | default    | —                                              |
| `alert`    | transient  | Times out after 4s                             |
| `happy`    | transient  | Times out after 6s                             |
| `excited`  | transient  | Times out after 5s                             |
| `sleepy`   | **sticky** | `ACTIVITY_RESUMED` event                       |
| `worried`  | **sticky** | `BATTERY_OK` event (battery-triggered only)    |

Sticky states persist until explicitly resolved rather than timing out, and
they can't be interrupted by a transient event — e.g. a brief CPU spike
won't visually cut off a `worried` (low-battery) expression.

## Built-in signals

| Signal              | Key (config.ini)     | Default | What it does                                                        |
|----------------------|-----------------------|---------|------------------------------------------------------------------------|
| `CpuSignal`          | `cpu_signal`          | on      | `psutil.cpu_percent()` crosses 75% → `alert`; drops below 45% → clears |
| `IdleTimeSignal`     | `idle_time_signal`    | on      | No aggregate input activity for `idle_sleepy_minutes` (default 10) → `sleepy` |
| `BatterySignal`      | `battery_signal`      | on      | Battery ≤ 20% and unplugged → `worried`; plugged in or charged → clears |
| `GitWatchSignal`     | `git_watch_signal`    | **off** | Polls `git rev-parse HEAD` in `git_watch_repo` → `happy` on new commit; optionally tails a build log for failure markers → `worried` |

All of these are configured under `[mood]` in `config.ini`:

```ini
[mood]
enabled = true
cpu_signal = true
idle_time_signal = true
battery_signal = true
git_watch_signal = false
git_watch_repo =
idle_sleepy_minutes = 10
```

## Writing a new signal

Subclass `MoodSignal` (`pixelpal/mood/signals/base.py`):

```python
from pixelpal.mood.signals.base import MoodSignal, MoodEvent, SignalReading

class PomodoroSignal(MoodSignal):
    key = "pomodoro_signal"

    def __init__(self, timer):
        self.timer = timer

    def poll(self) -> SignalReading:
        if self.timer.just_finished():
            return SignalReading(MoodEvent.HAPPY... )  # or a new MoodEvent
        return SignalReading(MoodEvent.NONE)
```

Then register it in `main.py`'s `build_mood_engine()`. If your signal needs
a genuinely new state transition, add the mapping to `_EVENT_TO_STATE` (or
`_RESOLVING_EVENTS` if it clears a sticky state) in `state_machine.py` —
everything else (transient timeout handling, sticky-state protection) is
handled generically.

## How mood affects rendering

`OverlayWindow._apply_mood()` (in `core/overlay_window.py`) is the only
place mood state touches rendering:

- `sleepy` → `EyeLayer.set_eyes_closed(True)` (shows `eyes.closed` sprite
  if the char pack defines one; otherwise pupils just keep rendering
  normally, since `closed` is optional).
- Any state with a matching key in the char pack's `expressions` map →
  `ExpressionLayer.set_mood()` swaps in that overlay sprite. States without
  an entry show nothing.

Debug tip: right-click → **Mood debug** → **Force: `<state>`** manually
overrides the state machine, useful for checking a new expression sprite
without waiting for the real signal to fire.
