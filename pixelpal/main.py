"""PixelPal entry point.

CLI args:
    --image PATH     Override body image/gif for the starting character (debug use)
    --pos X,Y        Start position, overrides saved config
    --wait SECONDS   Idle-hold duration before the next animation cycle
    --debug          Verbose logging + keeps a console attached on Windows
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from pixelpal.charpack.installer import CharPackInstallError, install_char_pack_from_zip
from pixelpal.charpack.loader import CharPackLoadError, discover_char_packs, load_char_pack
from pixelpal.core.config_store import ConfigStore
from pixelpal.core.overlay_window import OverlayWindow
from pixelpal.features.activity_tracker import ActivityTracker
from pixelpal.features.chat_window import ChatWindow
from pixelpal.features.ollama_chat import DEFAULT_HOST, DEFAULT_MODEL
from pixelpal.features.reminders import ReminderScheduler, load_reminders, save_reminders
from pixelpal.mood.signals.battery_signal import BatterySignal
from pixelpal.mood.signals.cpu_signal import CpuSignal
from pixelpal.mood.signals.git_watch_signal import GitWatchSignal
from pixelpal.mood.signals.idle_time_signal import IdleTimeSignal
from pixelpal.mood.state_machine import MoodEngine
from pixelpal.utils.platform_utils import bundled_path

logger = logging.getLogger("pixelpal")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="pixelpal", description="A layered desktop pet overlay.")
    parser.add_argument("--image", help="Override body image/gif path (debug use)")
    parser.add_argument("--pos", help="Start position as X,Y")
    parser.add_argument("--wait", type=float, help="Idle-hold seconds before next animation cycle")
    parser.add_argument("--debug", action="store_true", help="Verbose logging")
    parser.add_argument("--character", help="Character name to launch (default: last used / cat)")
    return parser.parse_args(argv)


def chars_dir() -> str:
    return bundled_path("chars")


def build_mood_engine(config_store: ConfigStore, tracker: ActivityTracker) -> MoodEngine:
    engine = MoodEngine()

    if config_store.get_bool("mood", "cpu_signal", True):
        engine.add_signal(CpuSignal())

    if config_store.get_bool("mood", "idle_time_signal", True):
        idle_minutes = config_store.get_float("mood", "idle_sleepy_minutes", 10.0)
        engine.add_signal(IdleTimeSignal(tracker, idle_minutes=idle_minutes))

    if config_store.get_bool("mood", "battery_signal", True):
        engine.add_signal(BatterySignal())

    if config_store.get_bool("mood", "git_watch_signal", False):
        repo = config_store.get("mood", "git_watch_repo", "")
        if repo:
            engine.add_signal(GitWatchSignal(repo_path=repo))

    return engine


class PixelPalApp:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self._install_sigint_handler()

        self.config_store = ConfigStore()
        self.activity_tracker = ActivityTracker()
        if self.config_store.get_bool("activity_tracker", "enabled", True):
            self.activity_tracker.start()

        self.mood_engine = build_mood_engine(self.config_store, self.activity_tracker)

        self.window: OverlayWindow | None = None
        self.chat_window: ChatWindow | None = None
        self._reminder_scheduler = None

        self._launch_character()
        self._setup_reminders()

    def _resolve_start_character(self) -> str:
        if self.args.character:
            return self.args.character
        return self.config_store.get("window", "character", "cat")

    def _launch_character(self) -> None:
        name = self._resolve_start_character()
        pack_dir = os.path.join(chars_dir(), name)

        try:
            pack = load_char_pack(pack_dir)
        except CharPackLoadError as exc:
            logger.warning("Failed to load '%s' (%s), falling back to first available pack.", name, exc)
            available = discover_char_packs(chars_dir())
            if not available:
                QMessageBox.critical(
                    None, "PixelPal", f"No valid character packs found in {chars_dir()}."
                )
                sys.exit(1)
            pack = available[0]

        if self.args.wait is not None:
            pack.config.wait_seconds = self.args.wait

        self.window = OverlayWindow(pack, self.config_store, mood_engine=self.mood_engine)
        self.window.available_characters_provider = self._available_characters
        self.window.set_callbacks(
            on_quit=self.app.quit,
            on_switch_character=self._switch_character,
            on_open_reminders=self._open_reminders_placeholder,
            on_open_ollama_settings=self._open_ollama_settings_placeholder,
            on_open_chat=self._open_chat,
            on_install_char_pack=self._install_char_pack,
        )

        if self.args.pos:
            try:
                x_str, y_str = self.args.pos.split(",")
                self.window.move(int(x_str), int(y_str))
            except ValueError:
                logger.warning("Ignoring malformed --pos value: %s", self.args.pos)

        self.window.show()

    def _available_characters(self) -> list[tuple[str, str]]:
        packs = discover_char_packs(chars_dir())
        return [(p.config.name, p.config.display_name) for p in packs]

    def _switch_character(self, name: str) -> None:
        pack_dir = os.path.join(chars_dir(), name)
        try:
            pack = load_char_pack(pack_dir)
        except CharPackLoadError as exc:
            QMessageBox.warning(None, "PixelPal", f"Could not load character '{name}':\n{exc}")
            return

        old_pos = self.window.pos()
        self.window.close()
        self.window = OverlayWindow(pack, self.config_store, mood_engine=self.mood_engine)
        self.window.available_characters_provider = self._available_characters
        self.window.set_callbacks(
            on_quit=self.app.quit,
            on_switch_character=self._switch_character,
            on_open_reminders=self._open_reminders_placeholder,
            on_open_ollama_settings=self._open_ollama_settings_placeholder,
            on_open_chat=self._open_chat,
            on_install_char_pack=self._install_char_pack,
        )
        self.window.move(old_pos)
        self.window.show()
        self.config_store.set_and_save("window", "character", name)

    def _install_char_pack(self) -> None:
        zip_path, _ = QFileDialog.getOpenFileName(None, "Install char pack", "", "Zip files (*.zip)")
        if not zip_path:
            return
        try:
            name = install_char_pack_from_zip(zip_path, chars_dir())
        except CharPackInstallError as exc:
            QMessageBox.warning(None, "PixelPal", f"Could not install char pack:\n{exc}")
            return
        QMessageBox.information(None, "PixelPal", f"Installed '{name}'. Switch to it from the right-click menu.")

    def _open_chat(self) -> None:
        if self.chat_window is not None:
            self.chat_window.close()
        host = self.config_store.get("ollama", "host", DEFAULT_HOST)
        model = self.config_store.get("ollama", "model", DEFAULT_MODEL)
        self.chat_window = ChatWindow(self.window.pack.config.display_name, host=host, model=model)
        self.chat_window.show()

    def _open_reminders_placeholder(self) -> None:
        # A full reminders-editing dialog is intentionally out of scope
        # for this pass; reminders.json can be hand-edited or the
        # add_daily_reminder / add_one_shot_reminder helpers used from
        # a script. This shows the current reminders as a quick summary.
        reminders = load_reminders()
        if not reminders:
            QMessageBox.information(
                None, "Reminders",
                "No reminders configured yet.\n\nAdd them via reminders.json in your config "
                "directory, or extend this dialog — see features/reminders.py."
            )
            return
        lines = [f"- [{r.kind}] {r.when}: {r.message}" for r in reminders]
        QMessageBox.information(None, "Reminders", "\n".join(lines))

    def _open_ollama_settings_placeholder(self) -> None:
        host = self.config_store.get("ollama", "host", DEFAULT_HOST)
        model = self.config_store.get("ollama", "model", DEFAULT_MODEL)
        QMessageBox.information(
            None, "Ollama settings",
            f"Host: {host}\nModel: {model}\n\nEdit these in config.ini under [ollama], "
            "then reopen the chat window."
        )

    def _setup_reminders(self) -> None:
        if not self.config_store.get_bool("reminders", "enabled", True):
            return

        reminders = load_reminders()

        def fire(reminder) -> None:  # noqa: ANN001
            from pixelpal.features.banner_widget import BannerWidget

            banner = BannerWidget(reminder.message)
            banner.show_and_animate()
            self._active_banner = banner  # keep a reference alive
            save_reminders(reminders)

        self._reminder_scheduler = ReminderScheduler(reminders, fire)

        self._reminder_timer = QTimer()
        self._reminder_timer.timeout.connect(self._reminder_scheduler.check)
        self._reminder_timer.start(30_000)

    def _install_sigint_handler(self) -> None:
        """Make Ctrl+C in the launching terminal actually quit the app.

        Qt's event loop (app.exec()) is native C++ code that blocks
        Python's interpreter, so Python never gets a chance to run its
        SIGINT handler when you press Ctrl+C. The fix: register a plain
        Python signal handler that calls app.quit(), and run a no-op
        QTimer on a short interval purely so the Python interpreter
        wakes up often enough to notice the signal was raised.
        """
        signal.signal(signal.SIGINT, lambda *_: self.app.quit())

        self._sigint_pump = QTimer()
        self._sigint_pump.timeout.connect(lambda: None)
        self._sigint_pump.start(200)

    def run(self) -> int:
        return self.app.exec()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)

    app = PixelPalApp(args)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
