"""Simple chat window for talking to the pet via local Ollama."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pixelpal.features.ollama_chat import (
    DEFAULT_PET_SYSTEM_PROMPT,
    ChatMessage,
    OllamaClient,
    OllamaError,
)


class _ChatWorker(QThread):
    reply_ready = Signal(str)
    error = Signal(str)

    def __init__(self, client: OllamaClient, history: list[ChatMessage]) -> None:
        super().__init__()
        self.client = client
        self.history = history

    def run(self) -> None:
        try:
            reply = self.client.chat(self.history, system_prompt=DEFAULT_PET_SYSTEM_PROMPT)
            self.reply_ready.emit(reply)
        except OllamaError as exc:
            self.error.emit(str(exc))


class ChatWindow(QWidget):
    def __init__(self, character_display_name: str, host: str, model: str) -> None:
        super().__init__()
        self.setWindowTitle(f"Chat with {character_display_name}")
        self.resize(360, 420)

        self.client = OllamaClient(host=host, model=model)
        self.history: list[ChatMessage] = []
        self._worker: _ChatWorker | None = None

        layout = QVBoxLayout(self)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        layout.addWidget(self.transcript)

        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(f"Say something to your {character_display_name.lower()}...")
        self.input_box.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_box)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._on_send)
        input_row.addWidget(self.send_button)

        layout.addLayout(input_row)

        self._check_availability()

    def _check_availability(self) -> None:
        if self.client.is_available():
            self.status_label.setText(f"Connected to Ollama ({self.client.model})")
        else:
            self.status_label.setText(
                "⚠ Ollama not reachable — run `ollama serve` locally to chat."
            )
            self.send_button.setEnabled(False)

    def _append_line(self, speaker: str, text: str) -> None:
        self.transcript.append(f"<b>{speaker}:</b> {text}")

    def _on_send(self) -> None:
        text = self.input_box.text().strip()
        if not text:
            return

        self.input_box.clear()
        self._append_line("You", text)
        self.history.append(ChatMessage(role="user", content=text))

        self.send_button.setEnabled(False)
        self.status_label.setText("Thinking...")

        self._worker = _ChatWorker(self.client, list(self.history))
        self._worker.reply_ready.connect(self._on_reply)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_reply(self, reply: str) -> None:
        self.history.append(ChatMessage(role="assistant", content=reply))
        self._append_line(self.windowTitle().replace("Chat with ", ""), reply)
        self.status_label.setText(f"Connected to Ollama ({self.client.model})")
        self.send_button.setEnabled(True)

    def _on_error(self, message: str) -> None:
        self._append_line("System", f"⚠ {message}")
        self.status_label.setText("Error — see message above")
        self.send_button.setEnabled(True)
