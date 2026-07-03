"""
Activation management page.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer

from app.widgets import (
    Colors, SectionHeader, SearchBar, StatusBadge, LoadingOverlay,
)
from app.seed_data import SeedData


class ActivationPage(QWidget):
    """Activation management page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = SectionHeader("✅ Activations", "Track license activations")
        header.add_action("Export", "📥", None, "outline")
        layout.addWidget(header)

        self.search = SearchBar("Search by license, customer, IP...")
        self.search.search_changed.connect(self._on_search)
        layout.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "License Key", "Machine FP", "Customer", "Status", "Activated", "IP", "Country"])
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

        self.loading = LoadingOverlay("Loading activations...", self)

    def _load_data(self) -> None:
        self.loading.show_overlay()
        QTimer.singleShot(200, self._populate)

    def _populate(self) -> None:
        self._data = SeedData.activations
        self._update_table()
        self.loading.hide_overlay()

    def _update_table(self, data: list = None) -> None:
        items = data or self._data
        self.table.setRowCount(len(items))
        for row, a in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(a.get("id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(a.get("license", "")[:20] + "..."))
            self.table.setItem(row, 2, QTableWidgetItem(a.get("machine", "")[:16] + "..."))
            self.table.setItem(row, 3, QTableWidgetItem(a.get("customer", "")))
            badge = StatusBadge(a.get("status", "active").upper(), a.get("status", "active"))
            self.table.setCellWidget(row, 4, badge)
            self.table.setItem(row, 5, QTableWidgetItem(a.get("activated_at", "")[:10]))
            self.table.setItem(row, 6, QTableWidgetItem(a.get("ip_address", "")))
            self.table.setItem(row, 7, QTableWidgetItem(a.get("country", "")))

    def _on_search(self, text: str) -> None:
        if not text:
            self._update_table(self._data)
            return
        text = text.lower()
        filtered = [a for a in self._data if text in a["license"].lower() or text in a["customer"].lower()]
        self._update_table(filtered)