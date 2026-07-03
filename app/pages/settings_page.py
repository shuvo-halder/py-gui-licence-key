"""
Settings page with multiple sections for configuration.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from app.widgets import (
    Colors, SectionHeader, card_style, button_style, input_style,
    InfoRow, ToastManager, ToastType,
)
from core.logger import get_logger

logger = get_logger(__name__)


class SettingsPage(QWidget):
    """Application settings page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = SectionHeader("⚙️ Settings", "Configure application settings")
        layout.addWidget(header)

        # Tab widget for settings sections
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 20px;
            }}
            QTabBar::tab {{
                background-color: {Colors.BG_LIGHT};
                color: {Colors.TEXT_SECONDARY};
                border: none;
                padding: 10px 20px;
                margin-right: 4px;
                border-radius: 8px 8px 0 0;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.PRIMARY};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """)

        tabs.addTab(self._general_tab(), "⚙️ General")
        tabs.addTab(self._security_tab(), "🔒 Security")
        tabs.addTab(self._database_tab(), "🗄️ Database")
        tabs.addTab(self._api_tab(), "🌐 API")
        tabs.addTab(self._theme_tab(), "🎨 Theme")
        tabs.addTab(self._backup_tab(), "💾 Backup")

        layout.addWidget(tabs, 1)

    def _section_card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setStyleSheet(card_style())
        cl = QVBoxLayout(card)
        cl.setSpacing(12)
        heading = QLabel(title)
        heading.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: 600; margin-bottom: 8px;")
        cl.addWidget(heading)
        return card, cl

    def _general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        card, cl = self._section_card("Application Settings")
        form = QFormLayout()
        form.setSpacing(10)

        app_name = QLineEdit("License Manager")
        app_name.setStyleSheet(input_style())
        form.addRow("Application Name:", app_name)

        version = QLineEdit("1.0.0")
        version.setStyleSheet(input_style())
        form.addRow("Version:", version)

        cl.addLayout(form)
        layout.addWidget(card)

        card2, cl2 = self._section_card("Notifications")
        notify = QCheckBox("Enable email notifications")
        notify.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px; spacing: 8px;")
        cl2.addWidget(notify)
        notify2 = QCheckBox("Enable webhook notifications")
        notify2.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px; spacing: 8px;")
        cl2.addWidget(notify2)
        auto_update = QCheckBox("Check for updates automatically")
        auto_update.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px; spacing: 8px;")
        cl2.addWidget(auto_update)
        layout.addWidget(card2)

        layout.addStretch()
        return w

    def _security_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        card, cl = self._section_card("Security Settings")
        info = InfoRow("Encryption", "AES-256-GCM")
        cl.addWidget(info)
        info2 = InfoRow("Key Length", "4096 bits")
        cl.addWidget(info2)
        info3 = InfoRow("Hash Algorithm", "SHA-256")
        cl.addWidget(info3)
        layout.addWidget(card)

        card2, cl2 = self._section_card("RSA Keys")
        gen_btn = QPushButton("🔄 Generate New RSA Key Pair")
        gen_btn.setStyleSheet(button_style(Colors.SECONDARY))
        cl2.addWidget(gen_btn)

        view_btn = QPushButton("👁 View Public Key")
        view_btn.setStyleSheet(button_style("outline"))
        cl2.addWidget(view_btn)
        layout.addWidget(card2)

        layout.addStretch()
        return w

    def _database_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        card, cl = self._section_card("Database Connection")
        form = QFormLayout()
        form.setSpacing(10)

        db_type = QComboBox()
        db_type.addItems(["SQLite", "PostgreSQL", "MySQL", "MSSQL"])
        db_type.setStyleSheet(input_style())
        form.addRow("Database Type:", db_type)

        host = QLineEdit("localhost")
        host.setStyleSheet(input_style())
        form.addRow("Host:", host)

        port = QLineEdit("5432")
        port.setStyleSheet(input_style())
        form.addRow("Port:", port)

        name = QLineEdit("license_manager")
        name.setStyleSheet(input_style())
        form.addRow("Database Name:", name)

        cl.addLayout(form)
        test_btn = QPushButton("🔌 Test Connection")
        test_btn.setStyleSheet(button_style(Colors.SUCCESS, Colors.SUCCESS_DARK))
        cl.addWidget(test_btn)
        layout.addWidget(card)

        card2, cl2 = self._section_card("Backup")
        backup_btn = QPushButton("💾 Create Database Backup")
        backup_btn.setStyleSheet(button_style(Colors.TEAL))
        cl2.addWidget(backup_btn)
        restore_btn = QPushButton("📂 Restore from Backup")
        restore_btn.setStyleSheet(button_style("outline"))
        cl2.addWidget(restore_btn)
        layout.addWidget(card2)

        layout.addStretch()
        return w

    def _api_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        card, cl = self._section_card("API Configuration")
        form = QFormLayout()
        form.setSpacing(10)

        api_url = QLineEdit("http://localhost:8000")
        api_url.setStyleSheet(input_style())
        form.addRow("API URL:", api_url)

        api_key = QLineEdit()
        api_key.setEchoMode(QLineEdit.Password)
        api_key.setPlaceholderText("Enter API key...")
        api_key.setStyleSheet(input_style())
        form.addRow("API Key:", api_key)

        cl.addLayout(form)
        test_btn = QPushButton("🌐 Test API Connection")
        test_btn.setStyleSheet(button_style(Colors.PRIMARY))
        cl.addWidget(test_btn)
        layout.addWidget(card)

        card2, cl2 = self._section_card("Rate Limiting")
        form2 = QFormLayout()
        rate = QSpinBox()
        rate.setRange(10, 10000)
        rate.setValue(1000)
        rate.setStyleSheet(input_style())
        form2.addRow("Requests per hour:", rate)
        cl2.addLayout(form2)
        layout.addWidget(card2)

        layout.addStretch()
        return w

    def _theme_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        card, cl = self._section_card("Theme Settings")
        form = QFormLayout()
        form.setSpacing(10)
        
        theme_combo = QComboBox()
        theme_combo.addItems(["Dark (Default)", "Light", "System", "High Contrast"])
        theme_combo.setStyleSheet(input_style())
        form.addRow("Theme:", theme_combo)

        accent_combo = QComboBox()
        accent_combo.addItems(["Blue (Default)", "Green", "Orange", "Purple", "Teal"])
        accent_combo.setStyleSheet(input_style())
        form.addRow("Accent Color:", accent_combo)
        cl.addLayout(form)

        apply_btn = QPushButton("Apply Theme")
        apply_btn.setStyleSheet(button_style())
        cl.addWidget(apply_btn)

        layout.addWidget(card)
        layout.addStretch()
        return w

    def _backup_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        card, cl = self._section_card("Backup & Restore")
        info = InfoRow("Last Backup", "2026-07-02 23:45:12")
        cl.addWidget(info)
        info2 = InfoRow("Backup Size", "156.3 MB")
        cl.addWidget(info2)
        info3 = InfoRow("Auto-backup", "Enabled (Daily)")
        cl.addWidget(info3)

        btn_layout = QHBoxLayout()
        backup_btn = QPushButton("💾 Create Backup Now")
        backup_btn.setStyleSheet(button_style(Colors.PRIMARY))
        btn_layout.addWidget(backup_btn)

        restore_btn = QPushButton("📂 Restore")
        restore_btn.setStyleSheet(button_style("outline"))
        btn_layout.addWidget(restore_btn)
        cl.addLayout(btn_layout)
        layout.addWidget(card)

        layout.addStretch()
        return w