"""
SDK Generator page for generating and managing client SDK packages.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from app.widgets import (
    Colors, SectionHeader, SearchBar, StatusBadge, LoadingOverlay,
    ProgressIndicator, card_style, button_style, input_style,
    Pagination, ExportMenu,
)
from app.seed_data import SeedData
from core.logger import get_logger

logger = get_logger(__name__)


class SdkPage(QWidget):
    """SDK Generator page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = SectionHeader("📥 SDK Generator", "Generate client integration packages")
        header.add_action("Generate SDK", "➕", self._generate_sdk, "primary")
        header.add_action("Regenerate", "🔄", None, "outline")
        layout.addWidget(header)

        # Progress indicator (hidden by default)
        self.progress = ProgressIndicator("Generating SDK package...", indeterminate=True)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Software", "Version", "Language", "Created", "Size", "Downloads"])
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

        self.pagination = Pagination()
        self.pagination.page_changed.connect(self._on_page)
        layout.addWidget(self.pagination)

        self.loading = LoadingOverlay("Loading SDK history...", self)

    def _load_data(self) -> None:
        self.loading.show_overlay()
        QTimer.singleShot(200, self._populate)

    def _populate(self) -> None:
        self._data = SeedData.sdk_history
        self.pagination.set_total_items(len(self._data))
        self._update_table()
        self.loading.hide_overlay()

    def _update_table(self) -> None:
        start = (self.pagination.current_page - 1) * self.pagination.per_page
        end = start + self.pagination.per_page
        page_data = self._data[start:end]
        self.table.setRowCount(len(page_data))
        for row, sdk in enumerate(page_data):
            self.table.setItem(row, 0, QTableWidgetItem(sdk.get("id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(sdk.get("software", "")))
            self.table.setItem(row, 2, QTableWidgetItem(sdk.get("version", "")))
            self.table.setItem(row, 3, QTableWidgetItem(sdk.get("language", "")))
            self.table.setItem(row, 4, QTableWidgetItem(sdk.get("created", "")[:10]))
            self.table.setItem(row, 5, QTableWidgetItem(sdk.get("size", "")))
            self.table.setItem(row, 6, QTableWidgetItem(str(sdk.get("downloads", 0))))

    def _generate_sdk(self) -> None:
        """Simulate SDK generation with progress."""
        self.progress.show()
        self.progress.set_text("Generating SDK package...")
        QTimer.singleShot(2000, self._generation_complete)

    def _generation_complete(self) -> None:
        self.progress.set_completed()
        QTimer.singleShot(1500, self.progress.hide)

    def _on_page(self, page: int) -> None:
        self._update_table()