from PySide6.QtCore import QObject, QThread, Signal

import bg_images
import config
import local_backgrounds
import weather_api


class _FetchSignals(QObject):
    succeeded = Signal(dict)
    failed = Signal(str)


class WeatherFetchWorker(QThread):
    """Runs location resolution + the Open-Meteo request off the UI thread.

    Usage:
        worker = WeatherFetchWorker()
        worker.succeeded.connect(on_data)
        worker.failed.connect(on_error)
        worker.start()
    """

    def __init__(self, cached_location: dict | None = None, parent=None):
        super().__init__(parent)
        self._signals = _FetchSignals()
        self.succeeded = self._signals.succeeded
        self.failed = self._signals.failed
        self._cached_location = cached_location

    def run(self):
        try:
            location = self._cached_location or weather_api.resolve_location()
            data = weather_api.fetch_weather(
                location["latitude"], location["longitude"], location["city"]
            )
            data["_location"] = location
            self.succeeded.emit(data)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            self.failed.emit(str(exc))


class BackgroundFetchWorker(QThread):
    """Resolves a background photo for a palette key, from whichever source
    config.BACKGROUND_SOURCE names ("local" folders, the paused "pexels"
    path, or neither).

    Emits `succeeded` with {'path', 'photographer', 'pexels_url'}
    (photographer/pexels_url are None for local photos - no credit needed
    for your own images) or `failed` if nothing was available - never
    raises into the UI thread. QPixmap itself is intentionally NOT
    constructed here; that happens back on the main thread.
    """

    def __init__(self, palette_key: str, avoid_path=None, parent=None):
        super().__init__(parent)
        self._signals = _FetchSignals()
        self.succeeded = self._signals.succeeded
        self.failed = self._signals.failed
        self.palette_key = palette_key
        self.avoid_path = avoid_path

    def run(self):
        source = config.BACKGROUND_SOURCE

        if source == "local":
            path = local_backgrounds.pick_local_background(self.palette_key, avoid=self.avoid_path)
            if path:
                self.succeeded.emit({"path": str(path), "photographer": None, "pexels_url": None})
            else:
                self.failed.emit("no local background photos supplied yet")
            return

        if source == "pexels":
            result = bg_images.fetch_background_for(self.palette_key)
            if result:
                self.succeeded.emit(result)
            else:
                self.failed.emit("no background photo available")
            return

        self.failed.emit("background photos turned off")
