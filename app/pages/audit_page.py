"""
Audit Log page with search, filter, and export.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from app.widgets import (
    Colors, SectionHeader, SearchBar, StatusBadge, LoadingOverlay,
    Pagination, card_style,
)
from app.seed_data import SeedData


class AuditPage(QWidget):
    """Audit log page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = SectionHeader("📝 Audit Logs", "Track all system activities")
        header.add_action("Export", "📥", None, "outline")
        header.add_action("Clear Logs", "🗑️", None, "outline")
        layout.addWidget(header)

        self.search = SearchBar("Search by action, user, IP, severity...")
        self.search.search_changed.connect(self._on_search)
        layout.addWidget(self.search)

        # Severity filter
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            background-color: {Colors.BG_LIGHT}; border: 1px solid {Colors.BORDER};
            border-radius: 10px; padding: 8px;
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        filter_layout.addWidget(QLabel("Severity:", styleSheet=f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;"))
        self.severity = QComboBox()
        self.severity.addItems(["All", "info", "warning", "error", "critical"])
        self.severity.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.BG_DARK}; color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER}; border-radius: 6px;
                padding: 6px 12px; font-size: 13px; min-width: 120px;
            }}
        """)
        self.severity.currentTextChanged.connect(self._on_filter)
        filter_layout.addWidget(self.severity)
        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Action", "User", "Severity", "IP", "Details"])
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

        self.loading = LoadingOverlay("Loading audit logs...", self)

    def _load_data(self) -> None:
        self.loading.show_overlay()
        QTimer.singleShot(200, self._populate)

    def _populate(self) -> None:
        self._data = SeedData.audit_logs
        self._filtered = self._data.copy()
        self.pagination.set_total_items(len(self._filtered))
        self._update_table()
        self.loading.hide_overlay()

    def _update_table(self) -> None:
        start = (self.pagination.current_page - 1) * self.pagination.per_page
        end = start + self.pagination.per_page
        page_data = self._filtered[start:end]
        self.table.setRowCount(len(page_data))
        for row, log in enumerate(page_data):
            self.table.setItem(row, 0, QTableWidgetItem(log.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(log.get("action", "")))
            self.table.setItem(row, 2, QTableWidgetItem(log.get("user", "")))

            severity = log.get("severity", "info")
            severity_colors = {"info": Colors.INFO, "warning": Colors.WARNING, "error": Colors.DANGER, "critical": Colors.DANGER}
            severity_bg = {"info": "rgba(0, 188, 212, 0.15)", "warning": "rgba(255, 193, 7, 0.15)",
                          "error": "rgba(244, 67, 54, 0.15)", "critical": "rgba(244, 67, 54, 0.3)"}
            color = severity_colors.get(severity, Colors.TEXT_SECONDARY)
            bg = severity_bg.get(severity, "rgba(176, 176, 176, 0.15)")
            badge = QLabel(severity.upper())
            badge.setStyleSheet(f"""
                background-color: {bg}; color: {color};
                border: 1px solid {color}33; border-radius: 8px;
                padding: 4px 10px; font-size: 11px; font-weight: 600;
            """)
            self.table.setCellWidget(row, 3, badge)
            self.table.setItem(row, 4, QTableWidgetItem(log.get("ip", "")))
            self.table.setItem(row, 5, QTableWidgetItem(log.get("details", "")))

    def _on_search(self, text: str) -> None:
        if not text:
            self._filtered = self._data.copy()
        else:
            t = text.lower()
            self._filtered = [l for l in self._data if t in str(l.get("action", "")).lower() or t in l.get("user", "").lower() or t in l.get("ip", "")]
        self.pagination.set_total_items(len(self._filtered))
        self._update_table()

    def _on_filter(self) -> None:
        sev = self.severity.currentText()
        if sev == "All":
            self._filtered = self._data.copy()
        else:
            self._filtered = [l for l in self._data if l.get("severity") == sev]
        self.pagination.set_total_items(len(self._filtered))
        self._update_table()

    def _on_page(self, page: int) -> None:
        self._update_table()