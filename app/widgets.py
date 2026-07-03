"""
Reusable UI widgets and components for the License Manager desktop application.

Provides custom widgets including stat cards, tables, dialogs, toast notifications,
loading indicators, empty states, and modern styled components.
"""

from __future__ import annotations

import math
from typing import Any, Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QTextEdit, QFormLayout, QGroupBox, QSizePolicy,
    QSpacerItem, QProgressBar, QGraphicsDropShadowEffect,
    QScrollArea, QStackedWidget, QMenu, QApplication,
    QDateEdit, QDateTimeEdit, QRadioButton, QButtonGroup,
    QSlider, QTabWidget, QSplitter, QToolButton,
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QTimer, QPropertyAnimation,
    QEasingCurve, QRect, QPoint, QSize, QThread,
    QParallelAnimationGroup, QSequentialAnimationGroup,
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QPainterPath, QFontDatabase, QIcon, QPixmap, QAction,
    QCursor, QPalette,
)

from core.logger import get_logger

logger = get_logger(__name__)


# ─── Color Palette ───────────────────────────────────────────────────────────

class Colors:
    """Application color palette."""
    PRIMARY = "#2196F3"
    PRIMARY_DARK = "#1976D2"
    PRIMARY_LIGHT = "#64B5F6"
    SECONDARY = "#FF9800"
    SECONDARY_DARK = "#F57C00"
    SUCCESS = "#4CAF50"
    SUCCESS_DARK = "#388E3C"
    DANGER = "#F44336"
    DANGER_DARK = "#D32F2F"
    WARNING = "#FFC107"
    WARNING_DARK = "#FFA000"
    INFO = "#00BCD4"
    PURPLE = "#9C27B0"
    TEAL = "#009688"
    
    BG_DARK = "#1E1E1E"
    BG_MEDIUM = "#252526"
    BG_LIGHT = "#2D2D2D"
    BG_HOVER = "#3A3A3A"
    BG_ACTIVE = "#424242"
    
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B0B0B0"
    TEXT_MUTED = "#666666"
    TEXT_DISABLED = "#424242"
    
    BORDER = "#3E3E3E"
    BORDER_LIGHT = "#333333"
    
    CARD_BG = "#2D2D2D"
    CARD_BORDER = "#3E3E3E"
    CARD_HOVER = "#333333"


# ─── Style Helpers ───────────────────────────────────────────────────────────

def card_style(border_left: str = None) -> str:
    """Generate card frame stylesheet."""
    border = f"border-left: 4px solid {border_left};" if border_left else ""
    return f"""
        QFrame {{
            background-color: {Colors.CARD_BG};
            border: 1px solid {Colors.CARD_BORDER};
            border-radius: 12px;
            {border}
            padding: 20px;
        }}
        QFrame:hover {{
            background-color: {Colors.CARD_HOVER};
        }}
    """


def button_style(bg: str = Colors.PRIMARY, hover: str = Colors.PRIMARY_DARK) -> str:
    """Generate button stylesheet."""
    return f"""
        QPushButton {{
            background-color: {bg};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {bg};
        }}
        QPushButton:disabled {{
            background-color: {Colors.BG_ACTIVE};
            color: {Colors.TEXT_MUTED};
        }}
    """


def input_style() -> str:
    """Generate input field stylesheet."""
    return f"""
        QLineEdit, QComboBox, QSpinBox, QTextEdit, QDateEdit, QDateTimeEdit {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus,
        QDateEdit:focus, QDateTimeEdit:focus {{
            border-color: {Colors.PRIMARY};
        }}
        QLineEdit::placeholder {{
            color: {Colors.TEXT_MUTED};
        }}
    """


# ─── Stat Card ───────────────────────────────────────────────────────────────

class StatCard(QFrame):
    """Modern statistics card with icon, value, trend, and mini chart."""

    clicked = Signal(str)

    def __init__(
        self,
        title: str,
        value: str,
        icon: str = "📊",
        color: str = Colors.PRIMARY,
        trend: str = "+0%",
        trend_up: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._value = value
        self._icon = icon
        self._color = color
        self._trend = trend
        self._trend_up = trend_up
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(card_style(self._color))
        self.setMinimumHeight(140)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Top row: icon + title
        top_row = QHBoxLayout()
        icon_label = QLabel(self._icon)
        icon_label.setStyleSheet("font-size: 28px;")
        top_row.addWidget(icon_label)

        title_lbl = QLabel(self._title)
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;")
        title_lbl.setWordWrap(True)
        top_row.addWidget(title_lbl, 1)
        layout.addLayout(top_row)

        # Value
        value_lbl = QLabel(self._value)
        value_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 32px; font-weight: 700;")
        layout.addWidget(value_lbl)

        # Bottom row: trend + mini chart placeholder
        bottom_row = QHBoxLayout()
        trend_color = Colors.SUCCESS if self._trend_up else Colors.DANGER
        trend_icon = "↑" if self._trend_up else "↓"
        trend_lbl = QLabel(f"{trend_icon} {self._trend}")
        trend_lbl.setStyleSheet(f"color: {trend_color}; font-size: 13px; font-weight: 600;")
        bottom_row.addWidget(trend_lbl)

        # Mini chart (simple bar representation)
        chart = MiniChart(color=self._color, parent=self)
        chart.setFixedSize(80, 30)
        bottom_row.addWidget(chart)

        layout.addLayout(bottom_row)

    def update_value(self, value: str, trend: str = None, trend_up: bool = None) -> None:
        """Update the card value and trend."""
        self._value = value
        if trend is not None:
            self._trend = trend
        if trend_up is not None:
            self._trend_up = trend_up
        # Rebuild would be needed for full update, but for simplicity:
        self.findChild(QLabel, "", Qt.FindChildrenRecursively).setText(value)

    def mousePressEvent(self, event):
        self.clicked.emit(self._title)
        super().mousePressEvent(event)


class MiniChart(QWidget):
    """Simple mini bar chart for stat cards."""

    def __init__(self, color: str = Colors.PRIMARY, parent=None):
        super().__init__(parent)
        self._color = color
        self._data = [0.3, 0.6, 0.4, 0.8, 0.5, 0.9, 0.7, 1.0, 0.6, 0.85]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        bar_count = len(self._data)
        bar_width = w / bar_count - 2

        for i, val in enumerate(self._data):
            bar_h = val * h * 0.8
            x = i * (bar_width + 2)
            y = h - bar_h

            color = QColor(self._color)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_h), 2, 2)

        painter.end()


# ─── Toast Notification ──────────────────────────────────────────────────────

class ToastType:
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ToastNotification(QFrame):
    """Floating toast notification with auto-dismiss."""

    def __init__(
        self,
        message: str,
        toast_type: str = ToastType.INFO,
        duration: int = 4000,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._message = message
        self._toast_type = toast_type
        self._duration = duration
        self._setup_ui()
        self._start_timer()

    def _setup_ui(self) -> None:
        colors = {
            ToastType.SUCCESS: (Colors.SUCCESS, "✅"),
            ToastType.ERROR: (Colors.DANGER, "❌"),
            ToastType.WARNING: (Colors.WARNING, "⚠️"),
            ToastType.INFO: (Colors.PRIMARY, "ℹ️"),
        }
        color, icon = colors.get(self._toast_type, (Colors.PRIMARY, "ℹ️"))

        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {color};
                border-left: 4px solid {color};
                border-radius: 10px;
                padding: 12px 16px;
            }}
        """)
        self.setFixedWidth(380)
        self.setMinimumHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_lbl)

        msg_lbl = QLabel(self._message)
        msg_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl, 1)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _start_timer(self) -> None:
        QTimer.singleShot(self._duration, self._fade_out)

    def _fade_out(self) -> None:
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()


class ToastManager:
    """Manages toast notifications in a container widget."""

    def __init__(self, parent: QWidget) -> None:
        self._parent = parent
        self._toasts: list[ToastNotification] = []

    def show_toast(
        self,
        message: str,
        toast_type: str = ToastType.INFO,
        duration: int = 4000,
    ) -> None:
        """Show a toast notification."""
        toast = ToastNotification(message, toast_type, duration, self._parent)
        toast.show()
        self._toasts.append(toast)
        self._reposition_toasts()

        toast.destroyed.connect(lambda: self._toasts.remove(toast))

    def _reposition_toasts(self) -> None:
        """Position toasts from bottom-right."""
        parent_rect = self._parent.rect()
        y_offset = parent_rect.height() - 80

        for toast in self._toasts:
            x = parent_rect.width() - toast.width() - 20
            toast.move(x, y_offset)
            y_offset -= toast.height() + 10


# ─── Loading Indicator ───────────────────────────────────────────────────────

class LoadingOverlay(QFrame):
    """Full-screen loading overlay with spinner and message."""

    def __init__(self, message: str = "Loading...", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._message = message
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            LoadingOverlay {{
                background-color: rgba(30, 30, 30, 200);
                border-radius: 0px;
            }}
        """)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Spinner
        self.spinner = QLabel("⏳")
        self.spinner.setStyleSheet("font-size: 48px;")
        self.spinner.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spinner)

        # Message
        msg_lbl = QLabel(self._message)
        msg_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: 600; margin-top: 16px;")
        msg_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_lbl)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setFixedWidth(200)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BG_DARK};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY};
                border-radius: 2px;
            }}
        """)
        progress_container = QHBoxLayout()
        progress_container.addStretch()
        progress_container.addWidget(self.progress)
        progress_container.addStretch()
        layout.addLayout(progress_container)

    def show_overlay(self, message: str = None) -> None:
        """Show the loading overlay."""
        if message:
            self._message = message
        self.raise_()
        self.show()
        QApplication.processEvents()

    def hide_overlay(self) -> None:
        """Hide the loading overlay."""
        self.hide()
        QApplication.processEvents()

    def resizeEvent(self, event):
        """Fill the parent widget."""
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)


# ─── Empty State ─────────────────────────────────────────────────────────────

class EmptyState(QWidget):
    """Empty state widget with icon, message, and action button."""

    action_clicked = Signal()

    def __init__(
        self,
        icon: str = "📂",
        title: str = "No data found",
        description: str = "There are no items to display.",
        action_text: str = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._icon = icon
        self._title = title
        self._description = description
        self._action_text = action_text
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # Icon
        icon_lbl = QLabel(self._icon)
        icon_lbl.setStyleSheet("font-size: 64px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # Title
        title_lbl = QLabel(self._title)
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 20px; font-weight: 600;")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        # Description
        desc_lbl = QLabel(self._description)
        desc_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px;")
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Action button
        if self._action_text:
            action_btn = QPushButton(self._action_text)
            action_btn.setStyleSheet(button_style())
            action_btn.setFixedWidth(200)
            action_btn.clicked.connect(self.action_clicked.emit)
            btn_container = QHBoxLayout()
            btn_container.addStretch()
            btn_container.addWidget(action_btn)
            btn_container.addStretch()
            layout.addLayout(btn_container)


# ─── Skeleton Loading ────────────────────────────────────────────────────────

class SkeletonWidget(QFrame):
    """Skeleton loading placeholder with shimmer animation."""

    def __init__(
        self,
        width: int = 200,
        height: int = 20,
        rounded: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setFixedSize(width, height)
        radius = 8 if rounded else 2
        self.setStyleSheet(f"""
            SkeletonWidget {{
                background-color: {Colors.BG_LIGHT};
                border-radius: {radius}px;
            }}
        """)


class SkeletonCard(QFrame):
    """Skeleton loading card with multiple lines."""

    def __init__(self, lines: int = 4, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(card_style())
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        for i in range(lines):
            w = [180, 240, 160, 200][i] if i < 4 else 200
            skeleton = SkeletonWidget(width=w, height=16)
            layout.addWidget(skeleton)


# ─── Search Bar ──────────────────────────────────────────────────────────────

class SearchBar(QFrame):
    """Modern search bar with icon and clear button."""

    search_changed = Signal(str)
    search_submitted = Signal(str)

    def __init__(
        self,
        placeholder: str = "Search...",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._placeholder = placeholder
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            SearchBar {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
            }}
            SearchBar:focus-within {{
                border-color: {Colors.PRIMARY};
            }}
        """)
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)

        icon_lbl = QLabel("🔍")
        icon_lbl.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_lbl)

        self.input = QLineEdit()
        self.input.setPlaceholderText(self._placeholder)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
                padding: 4px;
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}
        """)
        self.input.textChanged.connect(self.search_changed.emit)
        self.input.returnPressed.connect(lambda: self.search_submitted.emit(self.input.text()))
        layout.addWidget(self.input, 1)

        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_MUTED};
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self.clear_btn.clicked.connect(self._clear)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

        self.input.textChanged.connect(lambda t: self.clear_btn.setVisible(bool(t)))

    def _clear(self) -> None:
        self.input.clear()
        self.search_changed.emit("")

    def text(self) -> str:
        return self.input.text()

    def setText(self, text: str) -> None:
        self.input.setText(text)


# ─── Filter Bar ──────────────────────────────────────────────────────────────

class FilterBar(QFrame):
    """Horizontal filter bar with multiple filter options."""

    filters_changed = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._filters: dict[str, Any] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            FilterBar {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
                padding: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Status filter
        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(status_lbl)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Active", "Inactive", "Expired", "Revoked"])
        self.status_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                selection-background-color: {Colors.PRIMARY};
            }}
        """)
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.status_combo)

        # Date range
        layout.addWidget(QLabel("From:", styleSheet=f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setSpecialValueText("Any")
        self.date_from.setStyleSheet(input_style())
        self.date_from.dateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel("To:", styleSheet=f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setSpecialValueText("Any")
        self.date_to.setStyleSheet(input_style())
        self.date_to.dateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.date_to)

        layout.addStretch()

        # Clear filters
        clear_btn = QPushButton("Clear Filters")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY};
                color: white;
            }}
        """)
        clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(clear_btn)

    def _on_filter_changed(self) -> None:
        self._filters = {
            "status": self.status_combo.currentText(),
            "date_from": self.date_from.date().toString("yyyy-MM-dd") if not self.date_from.date().isNull() else None,
            "date_to": self.date_to.date().toString("yyyy-MM-dd") if not self.date_to.date().isNull() else None,
        }
        self.filters_changed.emit(self._filters)

    def _clear_filters(self) -> None:
        self.status_combo.setCurrentIndex(0)
        self.date_from.clear()
        self.date_to.clear()
        self._filters = {}
        self.filters_changed.emit(self._filters)

    def get_filters(self) -> dict:
        return self._filters


# ─── Pagination ──────────────────────────────────────────────────────────────

class Pagination(QFrame):
    """Pagination control with page numbers and navigation."""

    page_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_page = 1
        self._total_pages = 1
        self._total_items = 0
        self._per_page = 20
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            Pagination {{
                background-color: transparent;
                padding: 8px 0px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.info_label = QLabel("Showing 0-0 of 0")
        self.info_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(self.info_label)

        layout.addStretch()

        # Navigation buttons
        self.first_btn = self._nav_button("«")
        self.first_btn.clicked.connect(lambda: self._go_to_page(1))
        layout.addWidget(self.first_btn)

        self.prev_btn = self._nav_button("‹")
        self.prev_btn.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px; padding: 0 12px;")
        layout.addWidget(self.page_label)

        self.next_btn = self._nav_button("›")
        self.next_btn.clicked.connect(lambda: self._go_to_page(self._current_page + 1))
        layout.addWidget(self.next_btn)

        self.last_btn = self._nav_button("»")
        self.last_btn.clicked.connect(lambda: self._go_to_page(self._total_pages))
        layout.addWidget(self.last_btn)

        # Per page selector
        layout.addSpacing(16)
        layout.addWidget(QLabel("Per page:", styleSheet=f"color: {Colors.TEXT_MUTED}; font-size: 13px;"))
        self.per_page_combo = QComboBox()
        self.per_page_combo.addItems(["10", "20", "50", "100"])
        self.per_page_combo.setCurrentText("20")
        self.per_page_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 60px;
            }}
        """)
        self.per_page_combo.currentTextChanged.connect(self._on_per_page_changed)
        layout.addWidget(self.per_page_combo)

    def _nav_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(32, 32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {Colors.TEXT_DISABLED};
                border-color: transparent;
            }}
        """)
        return btn

    def _go_to_page(self, page: int) -> None:
        if page < 1 or page > self._total_pages or page == self._current_page:
            return
        self._current_page = page
        self._update_ui()
        self.page_changed.emit(page)

    def _on_per_page_changed(self, value: str) -> None:
        self._per_page = int(value)
        self._current_page = 1
        self._update_pages()
        self.page_changed.emit(self._current_page)

    def set_total_items(self, total: int) -> None:
        self._total_items = total
        self._update_pages()

    def _update_pages(self) -> None:
        self._total_pages = max(1, math.ceil(self._total_items / self._per_page))
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages
        self._update_ui()

    def _update_ui(self) -> None:
        start = (self._current_page - 1) * self._per_page + 1
        end = min(self._current_page * self._per_page, self._total_items)
        self.info_label.setText(f"Showing {start}-{end} of {self._total_items}")
        self.page_label.setText(f"Page {self._current_page} of {self._total_pages}")
        self.first_btn.setEnabled(self._current_page > 1)
        self.prev_btn.setEnabled(self._current_page > 1)
        self.next_btn.setEnabled(self._current_page < self._total_pages)
        self.last_btn.setEnabled(self._current_page < self._total_pages)

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def per_page(self) -> int:
        return self._per_page


# ─── Modern Table ────────────────────────────────────────────────────────────

class ModernTable(QFrame):
    """Modern styled table with custom features."""

    def __init__(
        self,
        columns: list[str],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._columns = columns
        self._data: list[list[Any]] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            ModernTable {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self._columns))
        self.table.setHorizontalHeaderLabels(self._columns)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 12px;
                gridline-color: {Colors.BORDER};
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {Colors.BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: rgba(33, 150, 243, 0.2);
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item:hover {{
                background-color: rgba(33, 150, 243, 0.1);
            }}
            QHeaderView::section {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                padding: 12px 14px;
                border: none;
                border-bottom: 2px solid {Colors.BORDER};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
        """)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setShowGrid(False)
        self.table.setMouseTracking(True)

        layout.addWidget(self.table)

    def set_data(self, data: list[list[Any]]) -> None:
        """Set table data."""
        self._data = data
        self.table.setRowCount(len(data))
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                if col < len(self._columns):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.table.setItem(row, col, item)

    def set_column_width(self, col: int, width: int) -> None:
        self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Interactive)
        self.table.setColumnWidth(col, width)

    def set_column_stretch(self, col: int) -> None:
        self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

    def get_selected_rows(self) -> list[int]:
        """Get indices of selected rows."""
        return {index.row() for index in self.table.selectedIndexes()}

    def clear(self) -> None:
        self.table.setRowCount(0)
        self._data = []

    @property
    def row_count(self) -> int:
        return self.table.rowCount()


# ─── Confirmation Dialog ─────────────────────────────────────────────────────

class ConfirmDialog(QDialog):
    """Modern confirmation dialog with custom styling."""

    def __init__(
        self,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_danger: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._message = message
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._confirm_danger = confirm_danger
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle(self._title)
        self.setFixedSize(420, 200)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_MEDIUM};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Icon
        icon_lbl = QLabel("⚠️" if self._confirm_danger else "ℹ️")
        icon_lbl.setStyleSheet("font-size: 36px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # Message
        msg_lbl = QLabel(self._message)
        msg_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 14px;")
        msg_lbl.setAlignment(Qt.AlignCenter)
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(self._cancel_text)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(self._confirm_text)
        confirm_color = Colors.DANGER if self._confirm_danger else Colors.PRIMARY
        confirm_hover = Colors.DANGER_DARK if self._confirm_danger else Colors.PRIMARY_DARK
        confirm_btn.setStyleSheet(button_style(confirm_color, confirm_hover))
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)


# ─── Section Header ──────────────────────────────────────────────────────────

class SectionHeader(QFrame):
    """Page section header with title, subtitle, and action buttons."""

    def __init__(
        self,
        title: str,
        subtitle: str = None,
        icon: str = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._subtitle = subtitle
        self._icon = icon
        self._action_buttons: list[QPushButton] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)

        # Icon + Title
        if self._icon:
            icon_lbl = QLabel(self._icon)
            icon_lbl.setStyleSheet("font-size: 28px; margin-right: 8px;")
            layout.addWidget(icon_lbl)

        title_layout = QVBoxLayout()
        title_lbl = QLabel(self._title)
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        title_layout.addWidget(title_lbl)

        if self._subtitle:
            sub_lbl = QLabel(self._subtitle)
            sub_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 13px;")
            title_layout.addWidget(sub_lbl)

        layout.addLayout(title_layout, 1)

        # Action buttons container
        self._actions_layout = QHBoxLayout()
        self._actions_layout.setSpacing(8)
        layout.addLayout(self._actions_layout)

    def add_action(
        self,
        text: str,
        icon: str = None,
        callback: Callable = None,
        style: str = "primary",
    ) -> QPushButton:
        """Add an action button to the header."""
        btn_text = f"{icon} {text}" if icon else text
        btn = QPushButton(btn_text)

        styles = {
            "primary": button_style(Colors.PRIMARY, Colors.PRIMARY_DARK),
            "secondary": button_style(Colors.SECONDARY, Colors.SECONDARY_DARK),
            "success": button_style(Colors.SUCCESS, Colors.SUCCESS_DARK),
            "danger": button_style(Colors.DANGER, Colors.DANGER_DARK),
            "outline": f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Colors.TEXT_SECONDARY};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {Colors.BG_HOVER};
                    color: {Colors.TEXT_PRIMARY};
                }}
            """,
        }
        btn.setStyleSheet(styles.get(style, styles["primary"]))
        if callback:
            btn.clicked.connect(callback)
        self._actions_layout.addWidget(btn)
        self._action_buttons.append(btn)
        return btn


# ─── Status Badge ────────────────────────────────────────────────────────────

class StatusBadge(QLabel):
    """Colored status badge."""

    def __init__(
        self,
        text: str,
        status: str = "active",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        colors = {
            "active": (Colors.SUCCESS, "rgba(76, 175, 80, 0.15)"),
            "inactive": (Colors.TEXT_MUTED, "rgba(102, 102, 102, 0.15)"),
            "expired": (Colors.DANGER, "rgba(244, 67, 54, 0.15)"),
            "revoked": (Colors.WARNING, "rgba(255, 193, 7, 0.15)"),
            "pending": (Colors.SECONDARY, "rgba(255, 152, 0, 0.15)"),
            "online": (Colors.SUCCESS, "rgba(76, 175, 80, 0.15)"),
            "offline": (Colors.TEXT_MUTED, "rgba(102, 102, 102, 0.15)"),
        }
        text_color, bg_color = colors.get(status, (Colors.TEXT_SECONDARY, "rgba(176, 176, 176, 0.15)"))

        self.setStyleSheet(f"""
            StatusBadge {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {text_color}33;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(26)


# ─── Progress Indicator ──────────────────────────────────────────────────────

class ProgressIndicator(QFrame):
    """Determinate or indeterminate progress bar with label."""

    def __init__(
        self,
        text: str = "Processing...",
        indeterminate: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._text = text
        self._indeterminate = indeterminate
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            ProgressIndicator {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Icon + Text
        row = QHBoxLayout()
        icon_lbl = QLabel("⏳")
        icon_lbl.setStyleSheet("font-size: 24px;")
        row.addWidget(icon_lbl)

        self.text_lbl = QLabel(self._text)
        self.text_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        row.addWidget(self.text_lbl, 1)
        layout.addLayout(row)

        # Progress bar
        self.progress = QProgressBar()
        if self._indeterminate:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BG_DARK};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress)

    def set_value(self, value: int) -> None:
        """Set progress value (0-100)."""
        if not self._indeterminate:
            self.progress.setValue(value)

    def set_text(self, text: str) -> None:
        self.text_lbl.setText(text)

    def set_completed(self) -> None:
        """Mark as completed."""
        self.text_lbl.setText("✅ Completed!")
        if not self._indeterminate:
            self.progress.setValue(100)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)


# ─── Info Row ────────────────────────────────────────────────────────────────

class InfoRow(QFrame):
    """Key-value information row for detail views."""

    def __init__(
        self,
        label: str,
        value: str,
        value_color: str = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._value = value
        self._value_color = value_color
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet("InfoRow { background-color: transparent; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)

        lbl = QLabel(self._label)
        lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 13px;")
        lbl.setFixedWidth(180)
        layout.addWidget(lbl)

        val = QLabel(self._value)
        color = self._value_color or Colors.TEXT_PRIMARY
        val.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 500;")
        val.setWordWrap(True)
        layout.addWidget(val, 1)

    def set_value(self, value: str) -> None:
        self.findChild(QLabel, "", Qt.FindChildrenRecursively).setText(value)


# ─── Export Button Group ─────────────────────────────────────────────────────

class ExportMenu(QPushButton):
    """Dropdown button for export options."""

    export_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("📥 Export", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)

        self._menu = QMenu(self)
        self._menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                color: {Colors.TEXT_PRIMARY};
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.PRIMARY};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Colors.BORDER};
                margin: 4px 8px;
            }}
        """)

        csv_action = QAction("📄 Export as CSV", self)
        csv_action.triggered.connect(lambda: self.export_requested.emit("csv"))
        self._menu.addAction(csv_action)

        excel_action = QAction("📊 Export as Excel", self)
        excel_action.triggered.connect(lambda: self.export_requested.emit("excel"))
        self._menu.addAction(excel_action)

        pdf_action = QAction("📕 Export as PDF", self)
        pdf_action.triggered.connect(lambda: self.export_requested.emit("pdf"))
        self._menu.addAction(pdf_action)

        self.setMenu(self._menu)


# ─── Avatar Widget ───────────────────────────────────────────────────────────

class AvatarWidget(QLabel):
    """Circular avatar with initials."""

    def __init__(
        self,
        name: str,
        size: int = 36,
        color: str = Colors.PRIMARY,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._name = name
        self._size = size
        self._color = color
        self._setup_ui()

    def _setup_ui(self) -> None:
        initials = "".join(word[0].upper() for word in self._name.split()[:2])
        self.setText(initials)
        self.setFixedSize(self._size, self._size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            AvatarWidget {{
                background-color: {self._color};
                color: white;
                border-radius: {self._size // 2}px;
                font-size: {self._size // 2}px;
                font-weight: 700;
            }}
        """)