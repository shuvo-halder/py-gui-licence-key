"""
Dashboard page - SaaS-style dashboard with stats, charts, and activity feed.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont

from app.widgets import (
    Colors, StatCard, SectionHeader, ToastManager, ToastType,
    LoadingOverlay, EmptyState, card_style, button_style,
    SkeletonCard, MiniChart, ExportMenu,
)
from app.seed_data import SeedData
from core.logger import get_logger

logger = get_logger(__name__)


class ChartWidget(QFrame):
    """Custom painted bar/line chart widget."""

    def __init__(self, title: str, chart_type: str = "bar", parent=None):
        super().__init__(parent)
        self._title = title
        self._chart_type = chart_type
        self._data: list[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            ChartWidget {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.CARD_BORDER};
                border-radius: 12px;
            }}
        """)
        self.setMinimumHeight(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel(self._title)
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        title_row.addWidget(title_lbl)

        title_row.addStretch()

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        for label, color in [("Series 1", Colors.PRIMARY), ("Series 2", Colors.SUCCESS)]:
            legend = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            legend.addWidget(dot)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
            legend.addWidget(lbl)
            legend_layout.addLayout(legend)
        title_row.addLayout(legend_layout)

        layout.addLayout(title_row)

        # Canvas area
        self.canvas = ChartCanvas(chart_type=self._chart_type)
        layout.addWidget(self.canvas, 1)

    def set_data(self, data: list[dict], value_key: str = "value", label_key: str = "label"):
        self._data = data
        self.canvas.set_data(data, value_key, label_key)
        self.canvas.update()


class ChartCanvas(QWidget):
    """Custom painted chart canvas."""

    def __init__(self, chart_type: str = "bar", parent=None):
        super().__init__(parent)
        self._chart_type = chart_type
        self._data: list[dict] = []
        self._value_key = "value"
        self._label_key = "label"
        self.setMinimumHeight(220)

    def set_data(self, data: list[dict], value_key: str = "value", label_key: str = "label"):
        self._data = data
        self._value_key = value_key
        self._label_key = label_key

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width() - 60
        h = self.height() - 60
        x0, y0 = 40, 20

        values = [d.get(self._value_key, 0) for d in self._data]
        max_val = max(values) if values else 1
        bar_count = len(self._data)
        bar_width = w // max(bar_count, 1) - 8

        colors = [Colors.PRIMARY, Colors.SUCCESS, Colors.SECONDARY, Colors.PURPLE, Colors.TEAL, Colors.INFO, Colors.WARNING]

        # Draw bars
        for i, d in enumerate(self._data):
            val = d.get(self._value_key, 0)
            bar_h = int((val / max_val) * h) if max_val > 0 else 0
            x = x0 + i * (bar_width + 8)
            y = y0 + h - bar_h

            color = QColor(colors[i % len(colors)])
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)

            if self._chart_type == "bar":
                path = self._rounded_rect(x, y, bar_width, bar_h, 4)
                painter.drawPath(path)
            elif self._chart_type == "line":
                painter.setBrush(Qt.NoBrush)
                pen = QPen(color, 3)
                painter.setPen(pen)
                if i > 0:
                    prev_val = self._data[i - 1].get(self._value_key, 0)
                    prev_h = int((prev_val / max_val) * h) if max_val > 0 else 0
                    prev_x = x0 + (i - 1) * (bar_width + 8) + bar_width // 2
                    prev_y = y0 + h - prev_h
                    painter.drawLine(prev_x, prev_y, x + bar_width // 2, y)

            # Value label
            painter.setPen(QPen(QColor(Colors.TEXT_SECONDARY)))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(x, y - 8, bar_width, 20, Qt.AlignCenter, str(val))

        # X-axis labels
        painter.setPen(QPen(QColor(Colors.TEXT_MUTED)))
        painter.setFont(QFont("Segoe UI", 8))
        for i, d in enumerate(self._data):
            label = d.get(self._label_key, "")
            x = x0 + i * (bar_width + 8) + bar_width // 2
            painter.drawText(x - 30, y0 + h + 8, 60, 30, Qt.AlignCenter, label)

        painter.end()

    def _rounded_rect(self, x, y, w, h, r):
        path = QPainterPath()
        path.addRoundedRect(x, y, w, h, r, r)
        return path


class ActivityFeed(QFrame):
    """Recent activity feed widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            ActivityFeed {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.CARD_BORDER};
                border-radius: 12px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("📋 Recent Activity")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()

        view_all = QPushButton("View All")
        view_all.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.PRIMARY};
                border: none;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ color: {Colors.PRIMARY_LIGHT}; }}
        """)
        header.addWidget(view_all)
        layout.addLayout(header)

        # Activity items
        activities = [
            ("🔑", "License Generated", "OfficeSuite Pro - Annual license", "2 min ago"),
            ("💻", "Machine Activated", "WS-005 on Windows 11 Pro", "15 min ago"),
            ("🔄", "Subscription Renewed", "CloudSync - Premium Plan", "1 hour ago"),
            ("📦", "Software Added", "NetworkMonitor v4.0.0", "3 hours ago"),
            ("📥", "SDK Generated", "DevToolKit Pro - Python SDK", "5 hours ago"),
            ("👤", "Customer Added", "Maria Garcia - Delos Inc", "1 day ago"),
            ("⚠️", "License Expiring", "DesignMaster - 3 days remaining", "2 days ago"),
        ]

        for icon, action, desc, time in activities:
            item = self._create_activity_item(icon, action, desc, time)
            layout.addWidget(item)

    def _create_activity_item(self, icon: str, action: str, desc: str, time: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_DARK};
                border-radius: 8px;
                padding: 4px;
            }}
            QFrame:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """)

        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        row.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        action_lbl = QLabel(action)
        action_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
        text_layout.addWidget(action_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px;")
        text_layout.addWidget(desc_lbl)
        row.addLayout(text_layout, 1)

        time_lbl = QLabel(time)
        time_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        row.addWidget(time_lbl)

        return frame


class DashboardPage(QWidget):
    """Main dashboard page with statistics, charts, and activity feed."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._loading = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {Colors.BG_MEDIUM};
            }}
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {Colors.BG_MEDIUM};")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)

        # Header with actions
        header = SectionHeader("📊 Dashboard", "Overview of your license management system")
        refresh_btn = header.add_action("Refresh", "🔄", self._refresh_data, "outline")
        export_btn = header.add_action("Export", "📥", self._export_dashboard, "outline")
        content_layout.addWidget(header)

        # Loading overlay
        self.loading = LoadingOverlay("Loading dashboard data...", scroll_content)

        # Stats cards grid
        self._stats_layout = QGridLayout()
        self._stats_layout.setSpacing(16)
        content_layout.addLayout(self._stats_layout)

        # Charts row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)

        self.license_chart = ChartWidget("📈 License Trend", "line")
        charts_layout.addWidget(self.license_chart, 1)

        self.revenue_chart = ChartWidget("💰 Revenue", "bar")
        charts_layout.addWidget(self.revenue_chart, 1)
        content_layout.addLayout(charts_layout)

        # Second charts row
        charts2_layout = QHBoxLayout()
        charts2_layout.setSpacing(16)

        self.subscription_chart = ChartWidget("📋 Subscriptions", "bar")
        charts2_layout.addWidget(self.subscription_chart, 1)

        self.activation_chart = ChartWidget("✅ Activations", "bar")
        charts2_layout.addWidget(self.activation_chart, 1)
        content_layout.addLayout(charts2_layout)

        # Activity feed
        self.activity_feed = ActivityFeed()
        content_layout.addWidget(self.activity_feed)

        content_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Populate with data
        QTimer.singleShot(100, self._load_data)

    def _load_data(self) -> None:
        """Load dashboard data."""
        self.loading.show_overlay("Loading dashboard...")

        # Simulate loading
        QTimer.singleShot(500, self._populate_stats)

    def _populate_stats(self) -> None:
        """Populate stats cards with seed data."""
        stats = SeedData.dashboard_stats()

        card_configs = [
            ("total_licenses", "🔑 Total Licenses", Colors.PRIMARY),
            ("active_licenses", "✅ Active Licenses", Colors.SUCCESS),
            ("expired_licenses", "❌ Expired Licenses", Colors.DANGER),
            ("revenue", "💰 Revenue", Colors.SECONDARY),
            ("active_machines", "💻 Active Machines", Colors.TEAL),
            ("registered_software", "📦 Registered Software", Colors.PURPLE),
            ("sdk_generated", "📥 SDK Generated", Colors.INFO),
            ("api_status", "🌐 API Status", Colors.SUCCESS),
        ]

        icons = ["🔑", "✅", "❌", "💰", "💻", "📦", "📥", "🌐"]
        for idx, (key, title, color) in enumerate(card_configs):
            stat = stats.get(key, {"value": "0", "trend": "+0%", "up": True})
            card = StatCard(
                title=title.split(" ", 1)[1] if " " in title else title,
                value=stat["value"],
                icon=title.split(" ")[0] if " " in title else "📊",
                color=color,
                trend=stat["trend"],
                trend_up=stat["up"],
            )
            row, col = divmod(idx, 4)
            self._stats_layout.addWidget(card, row, col)

        # Chart data
        monthly = SeedData.monthly_activations()
        revenue = SeedData.revenue_trend()

        self.license_chart.set_data(
            [{"label": d["month"], "value": d["activations"]} for d in monthly],
            value_key="value", label_key="label"
        )
        self.revenue_chart.set_data(
            [{"label": d["month"], "value": d["revenue"]} for d in revenue],
            value_key="value", label_key="label"
        )
        self.subscription_chart.set_data(
            [{"label": d["month"], "value": d["subscriptions"]} for d in revenue],
            value_key="value", label_key="label"
        )
        self.activation_chart.set_data(
            [{"label": d["month"], "value": d["activations"]} for d in monthly],
            value_key="value", label_key="label"
        )

        self.loading.hide_overlay()

    def _refresh_data(self) -> None:
        """Refresh dashboard data."""
        self._remove_existing_cards()
        self._populate_stats()

    def _remove_existing_cards(self) -> None:
        """Remove existing stat cards from the grid."""
        while self._stats_layout.count():
            item = self._stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _export_dashboard(self) -> None:
        """Export dashboard data."""
        logger.info("Dashboard export requested")