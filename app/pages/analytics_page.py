"""
Analytics page with charts, filters, and export.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont

from app.widgets import (
    Colors, SectionHeader, SearchBar, LoadingOverlay, card_style, button_style,
)
from app.pages.dashboard_page import ChartWidget
from app.seed_data import SeedData


class AnalyticsPage(QWidget):
    """Analytics and reporting page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = SectionHeader("📊 Analytics", "Insights and reporting")
        header.add_action("Export PDF", "📕", None, "outline")
        header.add_action("Export CSV", "📄", None, "outline")
        layout.addWidget(header)

        # Filter tabs
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background-color: {Colors.BG_LIGHT}; border-radius: 10px; padding: 8px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)

        filter_layout.addWidget(QLabel("Period:", styleSheet=f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;"))
        self.period = QComboBox()
        self.period.addItems(["Daily", "Weekly", "Monthly", "Yearly"])
        self.period.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.BG_DARK}; color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER}; border-radius: 6px;
                padding: 6px 12px; font-size: 13px; min-width: 120px;
            }}
        """)
        filter_layout.addWidget(self.period)
        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # Charts grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.activation_chart = ChartWidget("📈 Monthly Activations", "bar")
        grid.addWidget(self.activation_chart, 0, 0, 1, 2)

        self.revenue_chart = ChartWidget("💰 Revenue Trends", "line")
        grid.addWidget(self.revenue_chart, 0, 2, 1, 2)

        self.license_chart = ChartWidget("🔑 License Growth", "bar")
        grid.addWidget(self.license_chart, 1, 0, 1, 2)

        self.software_chart = ChartWidget("📦 Software Registrations", "bar")
        grid.addWidget(self.software_chart, 1, 2, 1, 2)

        layout.addLayout(grid, 1)

        self.loading = LoadingOverlay("Loading analytics...", self)

    def _load_data(self) -> None:
        self.loading.show_overlay()
        QTimer.singleShot(300, self._populate)

    def _populate(self) -> None:
        monthly = SeedData.monthly_activations()
        revenue = SeedData.revenue_trend()

        self.activation_chart.set_data(
            [{"label": d["month"], "value": d["activations"]} for d in monthly],
            value_key="value", label_key="label"
        )
        self.revenue_chart.set_data(
            [{"label": d["month"], "value": d["revenue"]} for d in revenue],
            value_key="value", label_key="label"
        )
        self.license_chart.set_data(
            [{"label": d["month"], "value": d["licenses"]} for d in revenue],
            value_key="value", label_key="label"
        )
        self.software_chart.set_data(
            [{"label": d["month"], "value": d["revenue"] / 1000} for d in revenue],
            value_key="value", label_key="label"
        )
        self.loading.hide_overlay()