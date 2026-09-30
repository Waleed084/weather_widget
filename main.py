"""
Desktop Weather Widget
=======================
A small, frameless, draggable, iOS-widget-style weather card that sits on
your Windows desktop. Location is detected automatically from your IP;
weather data comes from Open-Meteo (free, no API key).

Run:
    python main.py        (shows a console - useful while testing)
    pythonw main.py        (no console window - normal day-to-day use)

Right-click the card for Refresh / Keep-on-top / Quit. Left-click the tray
icon to show or hide the card.
"""
from __future__ import annotations

import sys
from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

import config
import styles
from widgets.weather_card import WeatherCard
from workers import WeatherFetchWorker, BackgroundFetchWorker


class WeatherApp:
    """Owns the card, the tray icon, the refresh timer, and the in-flight
    worker thread. Kept as one object so nothing gets garbage collected
    out from under a running QThread."""

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.card = WeatherCard(
            refresh_callback=self.refresh_now,
            quit_callback=self.quit,
        )
        self.card.show()

        self._location_cache: dict | None = None
        self._worker: WeatherFetchWorker | None = None
        self._bg_worker: BackgroundFetchWorker | None = None
        self._current_palette_key: str | None = None
        self._last_bg_path: Path | None = None

        self.tray = self._build_tray() if QSystemTrayIcon.isSystemTrayAvailable() else None

        self.timer = QTimer()
        self.timer.setInterval(config.REFRESH_INTERVAL_MS)
        self.timer.timeout.connect(self.refresh_now)
        self.timer.start()

        self.bg_timer = QTimer()
        self.bg_timer.setInterval(config.BACKGROUND_ROTATE_INTERVAL_MS)
        self.bg_timer.timeout.connect(self._rotate_background)
        self.bg_timer.start()

        # Kick off the first fetch immediately rather than waiting a full
        # interval for the card to populate.
        self.refresh_now()

    # -- tray ---------------------------------------------------------------
    def _build_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(qta.icon("fa5s.cloud-sun", color="#F0F3F7"))
        tray.setToolTip("Weather widget")

        menu = QMenu()
        toggle_action = menu.addAction("Show/Hide widget")
        toggle_action.triggered.connect(self._toggle_card_visibility)
        refresh_action = menu.addAction("Refresh now")
        refresh_action.triggered.connect(self.refresh_now)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_card_visibility()

    def _toggle_card_visibility(self):
        self.card.setVisible(not self.card.isVisible())

    # -- data flow ------------------------------------------------------------
    def refresh_now(self):
        if self._worker is not None and self._worker.isRunning():
            return  # a fetch is already in flight; don't overlap requests

        self._worker = WeatherFetchWorker(cached_location=self._location_cache)
        self._worker.succeeded.connect(self._on_fetch_succeeded)
        self._worker.failed.connect(self._on_fetch_failed)
        self._worker.start()

    def _on_fetch_succeeded(self, data: dict):
        self._location_cache = data.pop("_location", self._location_cache)
        self.card.update_weather(data)

        if self.tray:
            icon_color = styles.icon_color_for(data["icon_color_key"])
            self.tray.setIcon(qta.icon(data["icon"], color=icon_color))
            self.tray.setToolTip(
                f"{data['city']}: {data['temperature']}{data['units']} — {data['condition_label']}"
            )

        # Condition changed (or this is the first successful fetch) - fetch
        # a matching photo right away instead of waiting up to an hour.
        if data["palette_key"] != self._current_palette_key:
            self._current_palette_key = data["palette_key"]
            self._rotate_background()

    def _on_fetch_failed(self, message: str):
        self.card.show_error(message)
        if self.tray:
            self.tray.setToolTip(f"Weather widget — last refresh failed ({message})")

    # -- background photo rotation (config.BACKGROUND_SOURCE: local/pexels/off) --
    def _rotate_background(self):
        if config.BACKGROUND_SOURCE == "off" or not self._current_palette_key:
            return  # feature disabled, or we don't know the condition yet
        if self._bg_worker is not None and self._bg_worker.isRunning():
            return  # don't overlap image fetches

        self._bg_worker = BackgroundFetchWorker(self._current_palette_key, avoid_path=self._last_bg_path)
        self._bg_worker.succeeded.connect(self._on_background_succeeded)
        self._bg_worker.failed.connect(self._on_background_failed)
        self._bg_worker.start()

    def _on_background_succeeded(self, result: dict):
        pixmap = QPixmap(result["path"])
        if pixmap.isNull():
            return  # unreadable file - just keep whatever was already showing
        self._last_bg_path = Path(result["path"])
        self.card.set_background_photo(pixmap)
        self.card.set_photo_credit(result["photographer"], result["pexels_url"])

    def _on_background_failed(self, _message: str):
        pass  # keep whatever background (photo or gradient) is already showing

    # -- lifecycle ------------------------------------------------------------
    def quit(self):
        self.card.save_position()
        if self.tray:
            self.tray.hide()
        self.app.quit()

    def run(self) -> int:
        return self.app.exec()


def main() -> int:
    weather_app = WeatherApp()
    return weather_app.run()


if __name__ == "__main__":
    sys.exit(main())
