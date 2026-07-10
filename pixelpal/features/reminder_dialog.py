"""Add/view/delete reminders — a real UI on top of features/reminders.py's
pure scheduling logic.

Operates on the *same* list instance the running ReminderScheduler holds
(passed in by main.py), mutating it in place and saving to disk after
every change — so a reminder added here is picked up by the scheduler
immediately, with no restart needed.
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from pixelpal.features.reminders import (
    Reminder,
    add_daily_reminder,
    add_one_shot_reminder,
    save_reminders,
)


def _describe(reminder: Reminder) -> str:
    status = "" if reminder.enabled else "  (fired — one-time reminders don't repeat)"
    if reminder.kind == "daily":
        return f"Every day at {reminder.when} — {reminder.message}{status}"
    try:
        dt = datetime.fromisoformat(reminder.when)
        when_str = dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        when_str = reminder.when
    return f"Once, at {when_str} — {reminder.message}{status}"


class ReminderDialog(QWidget):
    def __init__(self, reminders: list[Reminder]) -> None:
        super().__init__()
        self.setWindowTitle("Reminders")
        self.resize(420, 420)
        self.reminders = reminders

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Your reminders:"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        delete_row = QHBoxLayout()
        delete_row.addStretch(1)
        self.delete_button = QPushButton("Delete selected")
        self.delete_button.clicked.connect(self._on_delete)
        delete_row.addWidget(self.delete_button)
        layout.addLayout(delete_row)

        layout.addWidget(QLabel("—" * 30))
        layout.addWidget(QLabel("Add a new reminder:"))

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("e.g. Stand up and stretch")
        layout.addWidget(self.message_input)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Repeats:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Daily", "One-time"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.type_combo)
        layout.addLayout(type_row)

        self.time_stack = QStackedWidget()

        daily_widget = QWidget()
        daily_layout = QHBoxLayout(daily_widget)
        daily_layout.addWidget(QLabel("Time each day:"))
        self.daily_time_edit = QTimeEdit(QTime.currentTime())
        self.daily_time_edit.setDisplayFormat("HH:mm")
        daily_layout.addWidget(self.daily_time_edit)
        self.time_stack.addWidget(daily_widget)

        once_widget = QWidget()
        once_layout = QHBoxLayout(once_widget)
        once_layout.addWidget(QLabel("Date:"))
        self.once_date_edit = QDateEdit(QDate.currentDate())
        self.once_date_edit.setCalendarPopup(True)
        once_layout.addWidget(self.once_date_edit)
        once_layout.addWidget(QLabel("Time:"))
        self.once_time_edit = QTimeEdit(QTime.currentTime())
        self.once_time_edit.setDisplayFormat("HH:mm")
        once_layout.addWidget(self.once_time_edit)
        self.time_stack.addWidget(once_widget)

        layout.addWidget(self.time_stack)

        self.add_button = QPushButton("Add reminder")
        self.add_button.clicked.connect(self._on_add)
        layout.addWidget(self.add_button)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e66;")
        layout.addWidget(self.error_label)

        self._refresh_list()

    def _on_type_changed(self, index: int) -> None:
        self.time_stack.setCurrentIndex(index)

    def _refresh_list(self) -> None:
        self.list_widget.clear()
        for reminder in self.reminders:
            item = QListWidgetItem(_describe(reminder))
            item.setData(Qt.UserRole, reminder.id)
            self.list_widget.addItem(item)

    def _on_add(self) -> None:
        message = self.message_input.text().strip()
        if not message:
            self.error_label.setText("Enter a message for the reminder first.")
            return

        if self.type_combo.currentText() == "Daily":
            t = self.daily_time_edit.time()
            add_daily_reminder(message, t.hour(), t.minute(), self.reminders)
        else:
            date = self.once_date_edit.date().toPython()
            time_ = self.once_time_edit.time()
            when = datetime(date.year, date.month, date.day, time_.hour(), time_.minute())
            if when <= datetime.now():
                self.error_label.setText("Pick a date/time in the future for a one-time reminder.")
                return
            add_one_shot_reminder(message, when, self.reminders)

        save_reminders(self.reminders)
        self.message_input.clear()
        self.error_label.setText("")
        self._refresh_list()

    def _on_delete(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        reminder_id = item.data(Qt.UserRole)
        self.reminders[:] = [r for r in self.reminders if r.id != reminder_id]
        save_reminders(self.reminders)
        self._refresh_list()
