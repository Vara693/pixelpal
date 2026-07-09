"""OS-specific quirks isolated in one place.

Keeping platform branching here (instead of scattered through core/)
means the rest of the app can just call e.g. `is_wayland()` without
caring how the detection is done.
"""

from __future__ import annotations

import os
import platform
import sys


def get_os() -> str:
    """Return one of 'windows', 'macos', 'linux'."""
    system = platform.system().lower()
    if system.startswith("win"):
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


def is_windows() -> bool:
    return get_os() == "windows"


def is_macos() -> bool:
    return get_os() == "macos"


def is_linux() -> bool:
    return get_os() == "linux"


def is_wayland() -> bool:
    """Best-effort Wayland detection on Linux."""
    if not is_linux():
        return False
    return (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        or bool(os.environ.get("WAYLAND_DISPLAY"))
    )


def has_x11_compositor() -> bool:
    """Best-effort check for a running compositing WM on X11.

    There's no fully reliable cross-DE way to check this from pure
    Python without extra deps, so we look for the common
    `_NET_WM_CM_S0` selection owner via `xprop`, falling back to
    "assume yes" if the check itself fails (fail open, since the
    degraded fallback path — clip-to-silhouette — is more expensive
    to render and shouldn't be forced on compositor-having systems).
    """
    if not is_linux() or is_wayland():
        return True

    try:
        import subprocess

        result = subprocess.run(
            ["xprop", "-root", "_NET_WM_CM_S0"],
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        return "not found" not in result.stdout and result.returncode == 0
    except Exception:
        return True


def supports_translucent_background() -> bool:
    """Whether Qt::WA_TranslucentBackground should behave correctly.

    On Linux without a compositor, translucency degrades to a black
    box, so the overlay window falls back to silhouette clipping
    instead (see core/overlay_window.py).
    """
    if is_windows() or is_macos():
        return True
    return has_x11_compositor()


def config_dir() -> str:
    """Return (and create) the platform-appropriate config directory."""
    if is_windows():
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        path = os.path.join(base, "PixelPal")
    elif is_macos():
        path = os.path.expanduser("~/Library/Application Support/PixelPal")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        path = os.path.join(base, "pixelpal")

    os.makedirs(path, exist_ok=True)
    return path


def runtime_dir() -> str:
    """Directory for ephemeral runtime files (multipet lock/registry)."""
    if is_linux():
        xdg = os.environ.get("XDG_RUNTIME_DIR")
        if xdg:
            path = os.path.join(xdg, "pixelpal")
            os.makedirs(path, exist_ok=True)
            return path
    import tempfile

    path = os.path.join(tempfile.gettempdir(), "pixelpal")
    os.makedirs(path, exist_ok=True)
    return path


def is_frozen() -> bool:
    """True when running from a PyInstaller-built binary."""
    return getattr(sys, "frozen", False)


def bundled_path(relative_path: str) -> str:
    """Resolve a path that works both in dev and in a PyInstaller bundle."""
    if is_frozen():
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base, relative_path)
