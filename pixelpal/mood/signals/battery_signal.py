"""Low-battery signal, via psutil.sensors_battery().

Degrades gracefully (always returns NONE) on desktops or platforms
where psutil can't report a battery.
"""

from __future__ import annotations

import psutil

from pixelpal.mood.signals.base import MoodEvent, MoodSignal, SignalReading


class BatterySignal(MoodSignal):
    key = "battery_signal"

    def __init__(self, low_threshold_percent: float = 20.0) -> None:
        self.low_threshold_percent = low_threshold_percent
        self._was_low = False

    def poll(self) -> SignalReading:
        try:
            battery = psutil.sensors_battery()
        except Exception:
            battery = None

        if battery is None:
            return SignalReading(MoodEvent.NONE)

        is_low = (not battery.power_plugged) and battery.percent <= self.low_threshold_percent

        if is_low and not self._was_low:
            self._was_low = True
            return SignalReading(MoodEvent.BATTERY_LOW, detail=f"{battery.percent:.0f}%")

        if not is_low and self._was_low:
            self._was_low = False
            return SignalReading(MoodEvent.BATTERY_OK, detail=f"{battery.percent:.0f}%")

        return SignalReading(MoodEvent.NONE)
