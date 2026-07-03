"""
Subscription management page.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer

from app.widgets import (
    Colors, SectionHeader, SearchBar, StatusBadge, ConfirmDialog,
    LoadingOverlay, button_style,
)
from app.seed_data import SeedData
from core.logger import get_logger

logger = get_logger(__name__)


class SubscriptionPage(QWidget):
    """Subscription management page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = SectionHeader("📋 Subscriptions", "Manage customer subscriptions")
        header.add_action("Add Subscription", "➕", None, "primary")
        header.add_action("Export", "📥", None, "outline")
        layout.addWidget(header)

        self.search = SearchBar("Search subscriptions...")
        self.search.search_changed.connect(self._on_search)
        layout.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Customer", "Product", "Plan", "Status", "Start", "End", "Amount", "Billing"])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                gridline-color: {Colors.BORDER};
                font-size: 13px;
            }}
            QTableWidget::item {{ padding: 10px 14px; border-bottom: 1px solid {Colors.BORDER}; }}
            QTableWidget::item:selected {{ background-color: rgba(33, 150, 243, 0.2); }}
            QHeaderView::section {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                padding: 12px 14px;
                border: none;
                border-bottom: 2px solid {Colors.BORDER};
                font-weight: 600;
                font-size: 12px;
            }}
        """)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setMinimumHeight(400)
        layout.addWidget(self.table, 1)

        self.loading = LoadingOverlay("Loading subscriptions...", self)

    def _load_data(self) -> None:
        self.loading.show_overlay()
        QTimer.singleShot(200, self._populate)

    def _populate(self) -> None:
        self._data = SeedData.subscriptions
        self._update_table()
        self.loading.hide_overlay()

    def _update_table(self, data: list = None) -> None:
        items = data or self._data
        self.table.setRowCount(len(items))
        for row, s in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(s.get("id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(s.get("customer", "")))
            self.table.setItem(row, 2, QTableWidgetItem(s.get("product", "")))
            self.table.setItem(row, 3, QTableWidgetItem(s.get("plan", "")))
            badge = StatusBadge(s.get("status", "active").upper(), s.get("status", "active"))
            self.table.setCellWidget(row, 4, badge)
            self.table.setItem(row, 5, QTableWidgetItem(s.get("start_date", "")[:10]))
            self.table.setItem(row, 6, QTableWidgetItem(s.get("end_date", "")[:10]))
            self.table.setItem(row, 7, QTableWidgetItem(f"${s.get('amount', 0):.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(s.get("billing", "")))

    def _on_search(self, text: str) -> None:
        if not text:
            self._update_table(self._data)
            return
        text = text.lower()
        filtered = [s for s in self._data if text in s["customer"].lower() or text in s["product"].lower()]
        self._update_table(filtered)