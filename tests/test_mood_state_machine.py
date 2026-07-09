from pixelpal.mood.signals.base import MoodEvent, MoodSignal, SignalReading
from pixelpal.mood.state_machine import MoodEngine, MoodState, TRANSIENT_STATE_HOLD_SECONDS


class ScriptedSignal(MoodSignal):
    """A test double that returns a pre-programmed sequence of readings."""

    key = "scripted"

    def __init__(self, readings: list[SignalReading]):
        self._readings = list(readings)
        self._index = 0

    def poll(self) -> SignalReading:
        if self._index >= len(self._readings):
            return SignalReading(MoodEvent.NONE)
        reading = self._readings[self._index]
        self._index += 1
        return reading


def test_starts_idle():
    engine = MoodEngine()
    assert engine.state == MoodState.IDLE


def test_cpu_spike_triggers_alert():
    signal = ScriptedSignal([SignalReading(MoodEvent.CPU_SPIKE)])
    engine = MoodEngine([signal])
    state = engine.tick()
    assert state == MoodState.ALERT


def test_battery_low_triggers_worried_and_is_sticky():
    signal = ScriptedSignal([
        SignalReading(MoodEvent.BATTERY_LOW),
        SignalReading(MoodEvent.CPU_SPIKE),  # should NOT override sticky WORRIED
    ])
    engine = MoodEngine([signal])
    engine.tick()
    assert engine.state == MoodState.WORRIED

    state = engine.tick()
    assert state == MoodState.WORRIED  # cpu spike did not override


def test_battery_ok_clears_worried():
    signal = ScriptedSignal([
        SignalReading(MoodEvent.BATTERY_LOW),
        SignalReading(MoodEvent.BATTERY_OK),
    ])
    engine = MoodEngine([signal])
    engine.tick()
    assert engine.state == MoodState.WORRIED

    engine.tick()
    assert engine.state == MoodState.IDLE


def test_idle_timeout_triggers_sleepy():
    signal = ScriptedSignal([SignalReading(MoodEvent.IDLE_TIMEOUT)])
    engine = MoodEngine([signal])
    state = engine.tick()
    assert state == MoodState.SLEEPY


def test_activity_resumed_clears_sleepy():
    signal = ScriptedSignal([
        SignalReading(MoodEvent.IDLE_TIMEOUT),
        SignalReading(MoodEvent.ACTIVITY_RESUMED),
    ])
    engine = MoodEngine([signal])
    engine.tick()
    assert engine.state == MoodState.SLEEPY
    engine.tick()
    assert engine.state == MoodState.IDLE


def test_git_commit_triggers_happy():
    signal = ScriptedSignal([SignalReading(MoodEvent.GIT_COMMIT)])
    engine = MoodEngine([signal])
    assert engine.tick() == MoodState.HAPPY


def test_build_failed_triggers_worried():
    signal = ScriptedSignal([SignalReading(MoodEvent.BUILD_FAILED)])
    engine = MoodEngine([signal])
    assert engine.tick() == MoodState.WORRIED


def test_transient_state_expires_after_hold_duration():
    signal = ScriptedSignal([SignalReading(MoodEvent.CPU_SPIKE)])
    engine = MoodEngine([signal])
    engine.tick()
    assert engine.state == MoodState.ALERT

    # Manually rewind the "entered at" clock to simulate time passing,
    # rather than sleeping in a unit test.
    hold = TRANSIENT_STATE_HOLD_SECONDS[MoodState.ALERT]
    engine._state_entered_at -= (hold + 1)

    state = engine.tick()
    assert state == MoodState.IDLE


def test_force_state_overrides_manually():
    engine = MoodEngine()
    engine.force_state(MoodState.EXCITED)
    assert engine.state == MoodState.EXCITED


def test_none_event_does_not_change_state():
    signal = ScriptedSignal([SignalReading(MoodEvent.NONE)])
    engine = MoodEngine([signal])
    assert engine.tick() == MoodState.IDLE
