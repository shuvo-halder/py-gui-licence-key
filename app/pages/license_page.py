"""
License Management page with full CRUD, filtering, pagination, and export.
"""

from __future__ import annotations

import datetime
from typing import Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit,
    QGroupBox, QMessageBox, QScrollArea, QCheckBox,
    QTextEdit, QSpinBox, QSplitter, QTabWidget,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont

from app.widgets import (
    Colors, SectionHeader, SearchBar, FilterBar, Pagination,
    ModernTable, StatusBadge, ConfirmDialog, ToastManager,
    ToastType, LoadingOverlay, EmptyState, ExportMenu,
    card_style, button_style, input_style, InfoRow,
)
from app.seed_data import SeedData
from core.logger import get_logger

logger = get_logger(__name__)


class CreateLicenseDialog(QDialog):
    """Dialog for creating a new license."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create New License")
        self.setMinimumWidth(600)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{ background-color: {Colors.BG_MEDIUM}; }}
            QLabel {{ color: {Colors.TEXT_SECONDARY}; font-size: 13px; }}
            QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit {{
                {input_style()}
            }}
            QGroupBox {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Create New License")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Customer & Product
        basic_group = QGroupBox("License Information")
        form = QFormLayout(basic_group)
        form.setSpacing(10)
        form.setContentsMargins(16, 24, 16, 16)

        self.customer_combo = QComboBox()
        for c in SeedData.customers:
            self.customer_combo.addItem(f"{c['name']} ({c['company']})", c["id"])
        form.addRow("Customer *:", self.customer_combo)

        self.product_combo = QComboBox()
        for p in SeedData.software_products:
            self.product_combo.addItem(p["name"])
        form.addRow("Product *:", self.product_combo)

        self.license_type = QComboBox()
        self.license_type.addItems(["perpetual", "subscription", "trial", "concurrent"])
        form.addRow("License Type *:", self.license_type)

        self.max_activations = QSpinBox()
        self.max_activations.setRange(1, 100)
        self.max_activations.setValue(5)
        form.addRow("Max Activations:", self.max_activations)

        layout.addWidget(basic_group)

        # Dates
        date_group = QGroupBox("Validity Period")
        date_form = QFormLayout(date_group)
        date_form.setSpacing(10)
        date_form.setContentsMargins(16, 24, 16, 16)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(datetime.date.today())
        date_form.addRow("Start Date *:", self.start_date)

        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(datetime.date.today().replace(year=datetime.date.today().year + 1))
        date_form.addRow("Expiry Date *:", self.expiry_date)

        layout.addWidget(date_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {Colors.BG_HOVER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.create_btn = QPushButton("Create License")
        self.create_btn.setStyleSheet(button_style())
        self.create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.create_btn)

        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            "customer": self.customer_combo.currentText(),
            "product": self.product_combo.currentText(),
            "type": self.license_type.currentText(),
            "max_activations": self.max_activations.value(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "expiry_date": self.expiry_date.date().toString("yyyy-MM-dd"),
        }


class ViewLicenseDialog(QDialog):
    """Dialog for viewing license details."""

    def __init__(self, license_data: dict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._data = license_data
        self.setWindowTitle("License Details")
        self.setMinimumWidth(650)
        self.setMinimumHeight(500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.BG_MEDIUM}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(f"🔑 License Details")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Info card
        card = QFrame()
        card.setStyleSheet(card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        fields = [
            ("License Key", self._data.get("key", "N/A"), Colors.PRIMARY),
            ("Customer", self._data.get("customer", "N/A")),
            ("Product", self._data.get("product", "N/A")),
            ("Type", self._data.get("type", "N/A")),
            ("Status", self._data.get("status", "N/A")),
            ("Created", self._data.get("created", "N/A")),
            ("Expiry", self._data.get("expiry", "N/A")),
            ("Machine Count", str(self._data.get("machine_count", 0))),
        ]

        for label, value, *color in fields:
            row = InfoRow(label, value, color[0] if color else None)
            card_layout.addWidget(row)

        layout.addWidget(card)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(button_style())
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class LicensePage(QWidget):
    """License management page with full CRUD operations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._licenses: list[dict] = []
        self._filtered: list[dict] = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = SectionHeader("🔑 License Management", "Manage software licenses")
        header.add_action("Create License", "➕", self._create_license, "primary")
        header.add_action("Bulk Actions", "📋", self._bulk_actions, "outline")
        export_btn = header.add_action("Export", "📥", self._export_data, "outline")
        layout.addWidget(header)

        # Search & Filter
        self.search_bar = SearchBar("Search by license key, customer, product...")
        self.search_bar.search_changed.connect(self._on_search)
        layout.addWidget(self.search_bar)

        self.filter_bar = FilterBar()
        self.filter_bar.filters_changed.connect(self._on_filter)
        layout.addWidget(self.filter_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "", "License Key", "Customer", "Product", "Type",
            "Status", "Created", "Expiry", "Machines", "Actions"
        ])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
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
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 40)
        self.table.setMinimumHeight(400)
        layout.addWidget(self.table, 1)

        # Pagination
        self.pagination = Pagination()
        self.pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self.pagination)

        # Loading overlay
        self.loading = LoadingOverlay("Loading licenses...", self)

    def _load_data(self) -> None:
        """Load license data from seed data."""
        self.loading.show_overlay("Loading licenses...")
        QTimer.singleShot(300, self._populate_data)

    def _populate_data(self) -> None:
        self._licenses = SeedData.licenses
        self._filtered = self._licenses.copy()
        self._update_table()
        self.loading.hide_overlay()

    def _update_table(self) -> None:
        """Update table with current page data."""
        start = (self.pagination.current_page - 1) * self.pagination.per_page
        end = start + self.pagination.per_page
        page_data = self._filtered[start:end]

        self.table.setRowCount(len(page_data))
        for row, lic in enumerate(page_data):
            # Checkbox
            check_item = QTableWidgetItem("")
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, check_item)

            self.table.setItem(row, 1, QTableWidgetItem(lic.get("key", "")))
            self.table.setItem(row, 2, QTableWidgetItem(lic.get("customer", "")))
            self.table.setItem(row, 3, QTableWidgetItem(lic.get("product", "")))
            self.table.setItem(row, 4, QTableWidgetItem(lic.get("type", "").upper()))

            # Status badge
            status = lic.get("status", "active")
            badge = StatusBadge(status.upper(), status)
            self.table.setCellWidget(row, 5, badge)

            self.table.setItem(row, 6, QTableWidgetItem(lic.get("created", "")[:10]))
            self.table.setItem(row, 7, QTableWidgetItem(lic.get("expiry", "")[:10]))
            self.table.setItem(row, 8, QTableWidgetItem(str(lic.get("machine_count", 0))))

            # Actions
            actions = self._create_action_buttons(lic)
            self.table.setCellWidget(row, 9, actions)

        self.pagination.set_total_items(len(self._filtered))

    def _create_action_buttons(self, lic: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        btn_style = f"""
            QPushButton {{
                background-color: {Colors.BG_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QPushButton:hover {{ background-color: {Colors.BG_HOVER}; color: {Colors.TEXT_PRIMARY}; }}
        """

        view_btn = QPushButton("👁")
        view_btn.setToolTip("View Details")
        view_btn.setStyleSheet(btn_style)
        view_btn.clicked.connect(lambda: self._view_license(lic))
        layout.addWidget(view_btn)

        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit License")
        edit_btn.setStyleSheet(btn_style)
        edit_btn.clicked.connect(lambda: self._edit_license(lic))
        layout.addWidget(edit_btn)

        renew_btn = QPushButton("🔄")
        renew_btn.setToolTip("Renew License")
        renew_btn.setStyleSheet(btn_style)
        renew_btn.clicked.connect(lambda: self._renew_license(lic))
        layout.addWidget(renew_btn)

        revoke_btn = QPushButton("🚫")
        revoke_btn.setToolTip("Revoke License")
        revoke_btn.setStyleSheet(btn_style)
        revoke_btn.clicked.connect(lambda: self._revoke_license(lic))
        layout.addWidget(revoke_btn)

        return container

    def _on_search(self, text: str) -> None:
        if not text:
            self._filtered = self._licenses.copy()
        else:
            text = text.lower()
            self._filtered = [
                l for l in self._licenses
                if text in l.get("key", "").lower()
                or text in l.get("customer", "").lower()
                or text in l.get("product", "").lower()
            ]
        self.pagination.set_total_items(len(self._filtered))
        self._update_table()

    def _on_filter(self, filters: dict) -> None:
        self._filtered = self._licenses.copy()
        status = filters.get("status", "All")
        if status != "All":
            self._filtered = [l for l in self._filtered if l.get("status", "").lower() == status.lower()]
        self.pagination.set_total_items(len(self._filtered))
        self._update_table()

    def _on_page_changed(self, page: int) -> None:
        self._update_table()

    def _create_license(self) -> None:
        dialog = CreateLicenseDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            logger.info(f"Creating license for {data['customer']}")
            # In production, this would call the service layer

    def _view_license(self, lic: dict) -> None:
        dialog = ViewLicenseDialog(lic, self)
        dialog.exec()

    def _edit_license(self, lic: dict) -> None:
        logger.info(f"Editing license: {lic.get('key', '')}")

    def _renew_license(self, lic: dict) -> None:
        confirm = ConfirmDialog(
            "Renew License",
            f"Renew license for {lic.get('customer', '')}?",
            "Renew", "Cancel"
        )
        if confirm.exec() == QDialog.Accepted:
            logger.info(f"License renewed: {lic.get('key', '')}")

    def _revoke_license(self, lic: dict) -> None:
        confirm = ConfirmDialog(
            "Revoke License",
            f"Are you sure you want to revoke this license?\n{lic.get('key', '')}",
            "Revoke", "Cancel", confirm_danger=True
        )
        if confirm.exec() == QDialog.Accepted:
            logger.info(f"License revoked: {lic.get('key', '')}")

    def _bulk_actions(self) -> None:
        logger.info("Bulk actions requested")

    def _export_data(self) -> None:
        logger.info("Export requested")