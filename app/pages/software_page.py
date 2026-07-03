"""
Software Registration page for managing registered applications.

This module provides the GUI for registering, editing, deleting,
and searching software products, as well as generating client SDKs.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QTextEdit, QFileDialog,
    QGroupBox, QSizePolicy, QSpacerItem, QProgressDialog,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor

from core.logger import get_logger

logger = get_logger(__name__)


class SoftwareFormDialog(QDialog):
    """Dialog for adding/editing a software product registration."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        product_data: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the form dialog.

        Args:
            parent: Parent widget.
            product_data: Existing product data for editing, or None for new.
        """
        super().__init__(parent)
        self.product_data = product_data
        self.setWindowTitle(
            "Edit Software Product" if product_data else "Register New Software"
        )
        self.setMinimumWidth(550)
        self.setModal(True)
        self._setup_ui()

        if product_data:
            self._populate_form(product_data)

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 13px;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border-color: #2196F3;
            }
            QCheckBox {
                color: #E0E0E0;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #5A5A5A;
                background-color: #1E1E1E;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            QGroupBox {
                color: #E0E0E0;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid #3E3E3E;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel(
            "Edit Software Product" if self.product_data
            else "Register New Software Product"
        )
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(title)

        # Basic Info Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(10)
        basic_layout.setContentsMargins(16, 24, 16, 16)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. My Application")
        basic_layout.addRow("Software Name *:", self.name_input)

        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("e.g. 1.0.0")
        basic_layout.addRow("Version *:", self.version_input)

        self.exe_name_input = QLineEdit()
        self.exe_name_input.setPlaceholderText("e.g. myapp.exe (for anti-tamper)")
        basic_layout.addRow("Executable Name:", self.exe_name_input)

        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Your Company Name")
        basic_layout.addRow("Company Name:", self.company_input)

        layout.addWidget(basic_group)

        # Licensing Group
        license_group = QGroupBox("License Configuration")
        license_layout = QFormLayout(license_group)
        license_layout.setSpacing(10)
        license_layout.setContentsMargins(16, 24, 16, 16)

        self.validation_combo = QComboBox()
        self.validation_combo.addItems(["online", "offline", "hybrid"])
        license_layout.addRow("Validation Type:", self.validation_combo)

        self.machine_lock_check = QCheckBox("Lock licenses to machine hardware")
        self.machine_lock_check.setChecked(True)
        license_layout.addRow("", self.machine_lock_check)

        self.max_activations_spin = QSpinBox()
        self.max_activations_spin.setRange(1, 9999)
        self.max_activations_spin.setValue(5)
        license_layout.addRow("Max Activations:", self.max_activations_spin)

        layout.addWidget(license_group)

        # Security Group
        security_group = QGroupBox("Security Features")
        security_layout = QVBoxLayout(security_group)
        security_layout.setSpacing(8)
        security_layout.setContentsMargins(16, 24, 16, 16)

        self.anti_tamper_check = QCheckBox(
            "Enable Anti-Tamper (validates executable integrity)"
        )
        self.anti_tamper_check.setChecked(True)
        security_layout.addWidget(self.anti_tamper_check)

        self.clock_protection_check = QCheckBox(
            "Enable Clock Manipulation Detection"
        )
        self.clock_protection_check.setChecked(True)
        security_layout.addWidget(self.clock_protection_check)

        layout.addWidget(security_group)

        # Feature Flags Group
        features_group = QGroupBox("Feature Flags")
        features_layout = QVBoxLayout(features_group)
        features_layout.setContentsMargins(16, 24, 16, 16)

        self.feature_flags_input = QTextEdit()
        self.feature_flags_input.setPlaceholderText(
            '["reporting", "ai_module", "export", "api_access"]'
        )
        self.feature_flags_input.setMaximumHeight(80)
        features_layout.addWidget(self.feature_flags_input)

        layout.addWidget(features_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E3E3E;
                color: #E0E0E0;
            }
            QPushButton:hover {
                background-color: #4E4E4E;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self.save_btn = QPushButton(
            "Update Product" if self.product_data else "Register Product"
        )
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #666666;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

        # Enable validation on name/version change
        self.name_input.textChanged.connect(self._validate_form)
        self.version_input.textChanged.connect(self._validate_form)

    def _validate_form(self) -> None:
        """Enable save button only when required fields are filled."""
        name = self.name_input.text().strip()
        version = self.version_input.text().strip()
        self.save_btn.setEnabled(bool(name and version))

    def _populate_form(self, data: dict[str, Any]) -> None:
        """Populate form fields with existing product data."""
        self.name_input.setText(data.get("name", ""))
        self.version_input.setText(data.get("version", ""))
        self.exe_name_input.setText(data.get("exe_name", "") or "")
        self.company_input.setText(data.get("company_name", "") or "")

        val_type = data.get("validation_type", "online")
        idx = self.validation_combo.findText(val_type)
        if idx >= 0:
            self.validation_combo.setCurrentIndex(idx)

        self.machine_lock_check.setChecked(data.get("machine_lock", True))
        self.max_activations_spin.setValue(data.get("max_activations", 5))
        self.anti_tamper_check.setChecked(data.get("anti_tamper", True))
        self.clock_protection_check.setChecked(data.get("clock_protection", True))

        feature_flags = data.get("feature_flags", "")
        self.feature_flags_input.setText(feature_flags or "")

    def get_form_data(self) -> dict[str, Any]:
        """Get the form data as a dictionary."""
        return {
            "name": self.name_input.text().strip(),
            "version": self.version_input.text().strip(),
            "exe_name": self.exe_name_input.text().strip() or None,
            "company_name": self.company_input.text().strip() or None,
            "validation_type": self.validation_combo.currentText(),
            "machine_lock": self.machine_lock_check.isChecked(),
            "max_activations": self.max_activations_spin.value(),
            "anti_tamper": self.anti_tamper_check.isChecked(),
            "clock_protection": self.clock_protection_check.isChecked(),
            "feature_flags": self.feature_flags_input.toPlainText().strip() or None,
        }


class SoftwarePage(QWidget):
    """Software Registration management page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the software management page."""
        super().__init__(parent)
        self.products: list[dict[str, Any]] = []
        self._service = None
        self._setup_ui()

    def _get_service(self):
        """Lazy import and create the service (avoids async init issues)."""
        if self._service is None:
            from database import async_session_factory
            from services.software_product.service import SoftwareProductService
            self._session = None
            self._service_ref = None
        return self._service

    def _setup_ui(self) -> None:
        """Setup the page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("📦 Software → Registered Apps")
        header.setStyleSheet("font-size: 24px; font-weight: 700; color: #FFFFFF;")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # SDK button
        self.sdk_btn = QPushButton("📦 Generate Client Integration Package")
        self.sdk_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #666666;
            }
        """)
        self.sdk_btn.clicked.connect(self._generate_sdk)
        self.sdk_btn.setEnabled(False)
        header_layout.addWidget(self.sdk_btn)

        # Add button
        self.add_btn = QPushButton("➕ Add New Software")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.add_btn.clicked.connect(self._add_software)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()

        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 18px;")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, company, app ID...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #3E3E3E;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Software Name", "Version", "App ID",
            "Product UUID", "Validation Mode", "Status", "Created", "Actions"
        ])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #3E3E3E;
                border-radius: 8px;
                gridline-color: #2D2D2D;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #2D2D2D;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid #3E3E3E;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }
        """)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(300)
        layout.addWidget(self.table)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Loading software products...")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

    def load_products(self, products: list[dict[str, Any]]) -> None:
        """Load products into the table."""
        self.products = products
        self._populate_table(products)
        self.sdk_btn.setEnabled(len(products) > 0)
        self.status_label.setText(
            f"Total: {len(products)} registered software product(s)"
        )

    def _populate_table(self, products: list[dict[str, Any]]) -> None:
        """Populate the table with product data."""
        self.table.setRowCount(len(products))

        for row, product in enumerate(products):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(product.get("name", "")))

            # Version
            self.table.setItem(row, 1, QTableWidgetItem(product.get("version", "")))

            # App ID (first 8 chars)
            app_id = product.get("app_id", "")
            self.table.setItem(row, 2, QTableWidgetItem(app_id[:8] + "..."))

            # Product UUID (first 8 chars)
            prod_id = product.get("id", "")
            self.table.setItem(row, 3, QTableWidgetItem(prod_id[:8] + "..."))

            # Validation Mode
            val_type = product.get("validation_type", "online")
            val_item = QTableWidgetItem(val_type.upper())
            if val_type == "online":
                val_item.setForeground(QColor("#4CAF50"))
            elif val_type == "offline":
                val_item.setForeground(QColor("#FF9800"))
            else:
                val_item.setForeground(QColor("#2196F3"))
            self.table.setItem(row, 4, val_item)

            # Status
            is_active = product.get("is_active", True)
            status_item = QTableWidgetItem("✅ Active" if is_active else "❌ Inactive")
            status_item.setForeground(QColor("#4CAF50") if is_active else QColor("#F44336"))
            self.table.setItem(row, 5, status_item)

            # Created
            created = product.get("created_at", "")
            if created:
                created = created[:10]
            self.table.setItem(row, 6, QTableWidgetItem(created))

            # Actions (Edit / Delete / SDK)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 28)
            edit_btn.setToolTip("Edit software product")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    border: 1px solid #3E3E3E;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #3E3E3E;
                }
            """)
            edit_btn.clicked.connect(
                lambda checked, pid=product.get("id", ""): self._edit_software(pid)
            )
            actions_layout.addWidget(edit_btn)

            sdk_btn = QPushButton("📦")
            sdk_btn.setFixedSize(32, 28)
            sdk_btn.setToolTip("Generate SDK for this product")
            sdk_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    border: 1px solid #F57C00;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            sdk_btn.clicked.connect(
                lambda checked, pid=product.get("id", ""): self._generate_sdk_for(pid)
            )
            actions_layout.addWidget(sdk_btn)

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(32, 28)
            del_btn.setToolTip("Delete software product")
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    border: 1px solid #3E3E3E;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #F44336;
                }
            """)
            del_btn.clicked.connect(
                lambda checked, pid=product.get("id", ""): self._delete_software(pid)
            )
            actions_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 7, actions_widget)

    def _add_software(self) -> None:
        """Open dialog to add a new software product."""
        dialog = SoftwareFormDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_form_data()
            logger.info(f"Adding software product: {data['name']}")
            self.product_added.emit(data)

    def _edit_software(self, product_id: str) -> None:
        """Open dialog to edit an existing software product."""
        product = next(
            (p for p in self.products if p.get("id") == product_id),
            None,
        )
        if not product:
            return

        dialog = SoftwareFormDialog(self, product_data=product)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_form_data()
            data["product_id"] = product_id
            logger.info(f"Updating software product: {product_id}")
            self.product_updated.emit(data)

    def _delete_software(self, product_id: str) -> None:
        """Delete a software product after confirmation."""
        product = next(
            (p for p in self.products if p.get("id") == product_id),
            None,
        )
        if not product:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f'Are you sure you want to delete "{product.get("name")}"?\n'
            "This action can be undone (soft delete).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            logger.info(f"Deleting software product: {product_id}")
            self.product_deleted.emit(product_id)

    def _on_search(self, text: str) -> None:
        """Filter the table by search text."""
        self.search_requested.emit(text)

    def _generate_sdk(self) -> None:
        """Generate SDK for the first selected product."""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            product_id = self.products[row].get("id", "")
            self._generate_sdk_for(product_id)
        elif self.products:
            # No selection, use first
            self._generate_sdk_for(self.products[0].get("id", ""))

    def _generate_sdk_for(self, product_id: str) -> None:
        """Generate client SDK for a specific product."""
        self.sdk_generate_requested.emit(product_id)

    def show_sdk_result(self, zip_path: str) -> None:
        """Show the result of SDK generation."""
        reply = QMessageBox.information(
            self,
            "SDK Generated",
            f"Client Integration Package generated successfully!\n\n"
            f"Location: {zip_path}\n\n"
            "You can now copy this package into your external software project.",
            QMessageBox.Ok | QMessageBox.Open,
        )
        if reply == QMessageBox.Open:
            # Open the containing folder
            folder = os.path.dirname(zip_path)
            os.startfile(folder)

    def show_error(self, message: str) -> None:
        """Show an error message."""
        QMessageBox.critical(self, "Error", message)

    def show_success(self, message: str) -> None:
        """Show a success message."""
        QMessageBox.information(self, "Success", message)

    # Signals
    product_added = Signal(dict)
    product_updated = Signal(dict)
    product_deleted = Signal(str)
    search_requested = Signal(str)
    sdk_generate_requested = Signal(str)