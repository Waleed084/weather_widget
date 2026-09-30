"""
WeatherCard: a single frameless, draggable, iOS-widget-style desktop card.

Layout (top to bottom):
    [location name]                              [stale dot]
    [icon]   [huge temperature]
             [condition label]
    [feels like]   [humidity]   [wind]
    [H / L today]                    [Open-Meteo attribution]
"""
from __future__ import annotations

import qtawesome as qta
from PySide6.QtCore import Qt, QRectF, QPointF, QSettings, QPoint, QUrl
from PySide6.QtGui import (
    QPainter, QPainterPath, QBrush, QColor, QPen, QFont, QCursor,
    QLinearGradient, QPixmap, QDesktopServices,
)
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect,
    QMenu, QSizePolicy,
)

import config
import styles


# ---------------------------------------------------------------------------
# The painted gradient surface + all drag / context-menu interaction.
# Every child label on top of it is mouse-transparent, so a click anywhere
# on the card reaches this frame - the whole card is the drag handle.
# ---------------------------------------------------------------------------
class GradientFrame(QFrame):
    def __init__(self, owner: "WeatherCard", parent=None):
        super().__init__(parent)
        self._owner = owner
        self._palette_key = "cloud_day"
        self._bg_pixmap: QPixmap | None = None
        self._drag_offset: QPoint | None = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

    def set_palette_key(self, key: str):
        if key != self._palette_key:
            self._palette_key = key
            self.update()

    def set_background_image(self, pixmap: QPixmap | None):
        """Swap in a real photo. Pass None to fall back to the procedural
        gradient (e.g. Pexels not configured, or a fetch failed)."""
        self._bg_pixmap = pixmap
        self.update()

    def clear_background_image(self):
        self.set_background_image(None)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, config.CORNER_RADIUS, config.CORNER_RADIUS)
        painter.setClipPath(path)  # corners stay round for photo OR gradient

        if self._bg_pixmap is not None and not self._bg_pixmap.isNull():
            scaled = self._bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)

            # Real photos have unpredictable brightness/business, so a
            # dedicated dark scrim keeps white text legible over any of
            # them - independent of the hand-tuned gradient stops below.
            scrim = QLinearGradient(QPointF(0, 0), QPointF(0, self.height()))
            scrim.setColorAt(0.0, QColor(0, 0, 0, 95))
            scrim.setColorAt(0.5, QColor(0, 0, 0, 55))
            scrim.setColorAt(1.0, QColor(0, 0, 0, 170))
            painter.fillRect(rect, QBrush(scrim))
        else:
            gradient = styles.make_gradient(self.width(), self.height(), self._palette_key)
            painter.fillPath(path, QBrush(gradient))

        painter.setClipping(False)
        # Faint 1px edge highlight for a bit of glassy depth, iOS-style.
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
        painter.drawPath(path)

    # -- drag-to-move -------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self._owner.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._owner.move(event.globalPosition().toPoint() - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._owner.save_position()
        event.accept()

    # -- right-click menu ----------------------------------------------
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        refresh_action = menu.addAction("Refresh now")
        top_action = menu.addAction(
            "Unpin from top" if self._owner.always_on_top else "Keep on top"
        )
        menu.addSeparator()
        quit_action = menu.addAction("Quit")

        chosen = menu.exec(event.globalPos())
        if chosen == refresh_action:
            self._owner.request_refresh()
        elif chosen == top_action:
            self._owner.toggle_always_on_top()
        elif chosen == quit_action:
            self._owner.request_quit()


# ---------------------------------------------------------------------------
# Small "icon + value" stat used for feels-like / humidity / wind.
# ---------------------------------------------------------------------------
class _StatChip(QWidget):
    def __init__(self, glyph: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._icon_label = QLabel(self)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        self._icon_label.setPixmap(qta.icon(glyph, color="#DCE3EC").pixmap(14, 14))

        self._value_label = QLabel("--", self)
        self._value_label.setStyleSheet(styles.label_qss(12, QFont.Weight.DemiBold, styles.TEXT_SECONDARY))

        layout.addWidget(self._icon_label)
        layout.addWidget(self._value_label)

    def set_text(self, text: str):
        self._value_label.setText(text)


# ---------------------------------------------------------------------------
# Tiny clickable attribution line - required credit-with-link for whichever
# source is currently active (Open-Meteo, or a Pexels photographer). This is
# the one label on the card that is NOT mouse-transparent, so this small
# corner isn't part of the drag handle - a fair trade for making the
# required credit link actually clickable.
# ---------------------------------------------------------------------------
class _LinkLabel(QLabel):
    def __init__(self, text: str, url: str, parent=None):
        super().__init__(text, parent)
        self._url = url
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_target(self, text: str, url: str):
        self.setText(text)
        self._url = url

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._url:
            QDesktopServices.openUrl(QUrl(self._url))
        event.accept()


# ---------------------------------------------------------------------------
# The public widget.
# ---------------------------------------------------------------------------
class WeatherCard(QWidget):
    def __init__(self, refresh_callback, quit_callback):
        super().__init__()
        self._refresh_callback = refresh_callback
        self._quit_callback = quit_callback
        self._last_good_data: dict | None = None
        self.always_on_top = config.ALWAYS_ON_TOP

        self.settings = QSettings(config.ORG_NAME, config.APP_NAME)

        total_w = config.CARD_WIDTH + 2 * config.SHADOW_MARGIN
        total_h = config.CARD_HEIGHT + 2 * config.SHADOW_MARGIN
        self.setFixedSize(total_w, total_h)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._apply_window_flags()

        self._build_ui()
        self._restore_position()
        self.show_loading()

    # -- window setup -----------------------------------------------------
    def _apply_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        was_visible = self.isVisible()
        self._apply_window_flags()
        if was_visible:
            self.show()

    def _build_ui(self):
        font_family = styles.pick_font_family()
        self.setFont(QFont(font_family))

        self.bg = GradientFrame(self, self)
        self.bg.setGeometry(
            config.SHADOW_MARGIN, config.SHADOW_MARGIN, config.CARD_WIDTH, config.CARD_HEIGHT
        )

        shadow = QGraphicsDropShadowEffect(self.bg)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 130))
        self.bg.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self.bg)
        outer.setContentsMargins(22, 18, 20, 16)
        outer.setSpacing(0)

        # --- header row: location .......... stale indicator
        header_row = QHBoxLayout()
        self.location_label = QLabel("Locating…", self.bg)
        self.location_label.setStyleSheet(styles.label_qss(14, QFont.Weight.DemiBold))
        self.location_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.stale_dot = QLabel("", self.bg)
        self.stale_dot.setFixedSize(8, 8)
        self.stale_dot.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.stale_dot.setStyleSheet(
            "background: rgba(255,196,84,0.9); border-radius: 4px;"
        )
        self.stale_dot.hide()

        header_row.addWidget(self.location_label)
        header_row.addStretch(1)
        header_row.addWidget(self.stale_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(header_row)

        outer.addSpacing(10)

        # --- hero row: icon | big temp + condition
        hero_row = QHBoxLayout()
        hero_row.setSpacing(14)

        self.icon_label = QLabel(self.bg)
        self.icon_label.setFixedSize(56, 56)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.icon_label.setStyleSheet("background: transparent; border: none;")

        temp_col = QVBoxLayout()
        temp_col.setSpacing(0)

        self.temp_label = QLabel("--°", self.bg)
        self.temp_label.setStyleSheet(styles.label_qss(52, QFont.Weight.Thin))
        self.temp_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.condition_label = QLabel("Loading weather…", self.bg)
        self.condition_label.setStyleSheet(styles.label_qss(13, QFont.Weight.Normal, styles.TEXT_SECONDARY))
        self.condition_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        temp_col.addWidget(self.temp_label)
        temp_col.addWidget(self.condition_label)

        hero_row.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)
        hero_row.addLayout(temp_col)
        hero_row.addStretch(1)
        outer.addLayout(hero_row)

        outer.addStretch(1)

        # --- stat row: feels like / humidity / wind
        stats_row = QHBoxLayout()
        stats_row.setSpacing(18)
        self.feels_chip = _StatChip("fa5s.thermometer-half", self.bg)
        self.humidity_chip = _StatChip("fa5s.tint", self.bg)
        self.wind_chip = _StatChip("fa5s.wind", self.bg)
        for chip in (self.feels_chip, self.humidity_chip, self.wind_chip):
            stats_row.addWidget(chip)
        stats_row.addStretch(1)
        outer.addLayout(stats_row)

        outer.addSpacing(10)

        # --- footer: high/low ........... attribution
        footer_row = QHBoxLayout()
        self.hilo_label = QLabel("H:-- L:--", self.bg)
        self.hilo_label.setStyleSheet(styles.label_qss(11, QFont.Weight.DemiBold, styles.TEXT_TERTIARY))
        self.hilo_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.attribution_label = _LinkLabel(config.ATTRIBUTION_TEXT, "https://open-meteo.com/", self.bg)
        self.attribution_label.setStyleSheet(styles.label_qss(9, QFont.Weight.Normal, styles.TEXT_TERTIARY))

        footer_row.addWidget(self.hilo_label)
        footer_row.addStretch(1)
        footer_row.addWidget(self.attribution_label)
        outer.addLayout(footer_row)

    # -- position persistence ---------------------------------------------
    def _restore_position(self):
        saved = self.settings.value("position")
        if saved is not None:
            self.move(saved)
            return
        screen = self.screen().availableGeometry() if self.screen() else None
        if screen:
            x = screen.right() - self.width() - config.START_POSITION_MARGIN
            y = screen.top() + config.START_POSITION_MARGIN
            self.move(x, y)

    def save_position(self):
        self.settings.setValue("position", self.pos())

    # -- state rendering ----------------------------------------------------
    def show_loading(self):
        self.bg.set_palette_key("cloud_day")
        self.icon_label.setPixmap(qta.icon("fa5s.cloud", color="#F0F3F7").pixmap(48, 48))

    def show_error(self, message: str):
        self.stale_dot.show()
        self.stale_dot.setToolTip(message)
        if self._last_good_data is None:
            self.location_label.setText("Couldn't load weather")
            self.condition_label.setText("Right-click → Refresh to retry")
            self.temp_label.setText("--°")

    def update_weather(self, data: dict):
        self._last_good_data = data
        self.stale_dot.hide()

        self.bg.set_palette_key(data["palette_key"])
        icon_color = styles.icon_color_for(data["icon_color_key"])
        self.icon_label.setPixmap(qta.icon(data["icon"], color=icon_color).pixmap(48, 48))

        self.location_label.setText(data["city"])
        self.temp_label.setText(f"{data['temperature']}{data['units']}")
        self.condition_label.setText(data["condition_label"])
        self.hilo_label.setText(f"H:{data['high']}°  L:{data['low']}°")

        self.feels_chip.set_text(f"{data['feels_like']}{data['units']}")
        self.humidity_chip.set_text(f"{data['humidity']}%")
        self.wind_chip.set_text(f"{data['wind_speed']} km/h")

    # -- photo backgrounds (optional, see bg_images.py) ----------------------
    def set_background_photo(self, pixmap: QPixmap):
        self.bg.set_background_image(pixmap)

    def clear_background_photo(self):
        self.bg.clear_background_image()
        self.set_photo_credit(None, None)

    def set_photo_credit(self, photographer: str | None, url: str | None):
        if photographer:
            self.attribution_label.set_target(
                f"Photo: {photographer} · Open-Meteo.com", url or "https://www.pexels.com"
            )
        else:
            self.attribution_label.set_target(config.ATTRIBUTION_TEXT, "https://open-meteo.com/")

    # -- glue back to main.py ----------------------------------------------
    def request_refresh(self):
        self._refresh_callback()

    def request_quit(self):
        self._quit_callback()
