"""Lightweight system audio amplitude polling for the (opt-in) ear twitch.

Deliberately NOT full audio capture/recording — this samples very
short buffers purely to compute a peak amplitude level in [0, 1] and
immediately discards the audio data. No audio is ever written to disk
or retained beyond the current sample.

Uses `sounddevice` if available (optional extra, not a hard
dependency of the base app so PixelPal still runs without it — the
ear layer just stays disabled). Falls back to a no-op monitor that
always reports 0.0 if the library or an input device isn't available,
matching the "off by default, opt-in, degrade gracefully" requirement.
"""

from __future__ import annotations

import threading


class AudioLevelMonitor:
    """Base/no-op monitor: always reports silence.

    Used automatically when the optional sounddevice dependency isn't
    installed, or when audio_reactive is disabled in settings.
    """

    def current_level(self) -> float:
        return 0.0

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


class SoundDeviceLevelMonitor(AudioLevelMonitor):
    """Real monitor backed by `sounddevice`, if installed.

    Install with: pip install pixelpal[audio]  (or `pip install sounddevice`)
    """

    def __init__(self, sample_rate: int = 16000, block_size: int = 512) -> None:
        self._lock = threading.Lock()
        self._level = 0.0
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._stream = None

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        import numpy as np

        peak = float(np.abs(indata).max()) if frames else 0.0
        with self._lock:
            self._level = min(1.0, peak)

    def start(self) -> None:
        try:
            import sounddevice as sd
        except Exception:
            return

        try:
            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                blocksize=self._block_size,
                channels=1,
                callback=self._callback,
            )
            self._stream.start()
        except Exception:
            self._stream = None

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def current_level(self) -> float:
        with self._lock:
            return self._level


def create_audio_monitor(enabled: bool) -> AudioLevelMonitor:
    """Factory respecting the opt-in setting; used by main.py wiring."""
    if not enabled:
        return AudioLevelMonitor()

    try:
        import sounddevice  # noqa: F401
    except Exception:
        return AudioLevelMonitor()

    monitor = SoundDeviceLevelMonitor()
    monitor.start()
    return monitor
