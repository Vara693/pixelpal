"""CPU usage spike signal, via psutil."""

from __future__ import annotations

import psutil

from pixelpal.mood.signals.base import MoodEvent, MoodSignal, SignalReading


class CpuSignal(MoodSignal):
    key = "cpu_signal"

    def __init__(self, spike_threshold: float = 75.0, recover_threshold: float = 45.0) -> None:
        self.spike_threshold = spike_threshold
        self.recover_threshold = recover_threshold
        self._was_spiking = False

    def start(self) -> None:
        # Prime psutil's internal sample window; first call to
        # cpu_percent() after this returns a meaningful delta instead
        # of 0.0.
        psutil.cpu_percent(interval=None)

    def poll(self) -> SignalReading:
        usage = psutil.cpu_percent(interval=None)

        if not self._was_spiking and usage >= self.spike_threshold:
            self._was_spiking = True
            return SignalReading(MoodEvent.CPU_SPIKE, detail=f"{usage:.0f}%")

        if self._was_spiking and usage <= self.recover_threshold:
            self._was_spiking = False
            return SignalReading(MoodEvent.CPU_NORMAL, detail=f"{usage:.0f}%")

        return SignalReading(MoodEvent.NONE)
