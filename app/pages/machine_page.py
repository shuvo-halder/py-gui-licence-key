"""
Machine management page.
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


class MachinePage(QWidget):
    """Machine management page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = SectionHeader("💻 Machine Management", "Manage registered machines")
        header.add_action("Export", "📥", None, "outline")
        layout.addWidget(header)

        self.search = SearchBar("Search by hostname, fingerprint, OS...")
        self.search.search_changed.connect(self._on_search)
        layout.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Hostname", "OS", "CPU", "RAM", "License", "Activation", "Status"])
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

        self.loading = LoadingOverlay("Loading machines...", self)

    def _load_data(self) -> None:
        self.loading.show_overlay()
        QTimer.singleShot(200, self._populate)

    def _populate(self) -> None:
        self._data = SeedData.machines
        self._update_table()
        self.loading.hide_overlay()

    def _update_table(self, data: list = None) -> None:
        items = data or self._data
        self.table.setRowCount(len(items))
        for row, m in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(m.get("id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(m.get("hostname", "")))
            self.table.setItem(row, 2, QTableWidgetItem(m.get("os", "")))
            self.table.setItem(row, 3, QTableWidgetItem(m.get("cpu", "")))
            self.table.setItem(row, 4, QTableWidgetItem(m.get("ram", "")))
            self.table.setItem(row, 5, QTableWidgetItem(m.get("license", "")[:16] + "..."))
            self.table.setItem(row, 6, QTableWidgetItem(m.get("activation_date", "")[:10]))
            badge = StatusBadge(m.get("status", "active").upper(), m.get("status", "active"))
            self.table.setCellWidget(row, 7, badge)

    def _on_search(self, text: str) -> None:
        if not text:
            self._update_table(self._data)
            return
        text = text.lower()
        filtered = [m for m in self._data if text in m["hostname"].lower() or text in m["os"].lower()]
        self._update_table(filtered)