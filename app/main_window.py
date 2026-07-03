"""
Main application window - Enterprise License Manager Desktop.

Provides a modern dark-themed interface with top header bar,
animated sidebar navigation, stacked pages, theme switching,
and server connection status.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QApplication, QSizePolicy, QSpacerItem, QLineEdit,
    QDialog, QMessageBox, QGraphicsDropShadowEffect,
    QScrollArea, QToolButton, QMenu, QSystemTrayIcon,
)
from PySide6.QtCore import (
    Qt, QSize, Signal, Slot, QTimer, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QRect,
)
from PySide6.QtGui import (
    QFont, QIcon, QPalette, QColor, QAction, QPixmap,
    QPainter, QBrush, QPen, QLinearGradient, QFontDatabase,
    QCursor,
)

from core.config import settings
from core.constants import Constants
from core.logger import get_logger

from app.widgets import (
    Colors, AvatarWidget, ToastManager, ToastType,
    button_style, card_style, input_style, SearchBar,
)
from app.pages import (
    DashboardPage, LicensePage, CustomerPage, MachinePage,
    SubscriptionPage, ActivationPage, AnalyticsPage,
    AuditPage, SettingsPage, SdkPage, SoftwarePage,
)

logger = get_logger(__name__)


# ─── Sidebar Button ──────────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    """Animated sidebar navigation button with icon and hover effects."""

    def __init__(self, text: str, icon: str = "", shortcut: str = "", parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self._icon = icon
        self._shortcut = shortcut
        self._collapsed = False
        self.setCheckable(True)
        self.setMinimumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

    def _update_style(self) -> None:
        padding = "12px 16px" if self._collapsed else "12px 16px 12px 20px"
        text_align = "center" if self._collapsed else "left"
        fg = f"{self._icon} " if self._icon else ""
        self.setText(f"{fg}{self._text}" if not self._collapsed else self._icon)
        self.setToolTip(f"{self._text} ({self._shortcut})" if self._shortcut else self._text)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 8px;
                padding: {padding};
                text-align: {text_align};
                font-size: 14px;
                font-weight: 500;
                margin: 2px 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: rgba(33, 150, 243, 0.15);
                color: {Colors.PRIMARY};
                font-weight: 600;
                border-left: 3px solid {Colors.PRIMARY};
            }}
        """)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._update_style()

    def set_active(self, active: bool) -> None:
        self.setChecked(active)


# ─── Sidebar ─────────────────────────────────────────────────────────────────

class Sidebar(QFrame):
    """Expandable sidebar with navigation items and smooth animation."""

    page_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._expanded = True
        self._expanded_width = 260
        self._collapsed_width = 72
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFixedWidth(self._expanded_width)
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {Colors.BG_DARK};
                border-right: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar header with collapse button
        header = QFrame()
        header.setStyleSheet(f"background-color: {Colors.BG_LIGHT}; border-bottom: 1px solid {Colors.BORDER_LIGHT};")
        header.setFixedHeight(64)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        self.logo_label = QLabel("🔐")
        self.logo_label.setStyleSheet("font-size: 28px;")
        header_layout.addWidget(self.logo_label)

        self.title_label = QLabel("License\nManager")
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 14px; font-weight: 700; line-height: 1.2;")
        header_layout.addWidget(self.title_label, 1)

        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_HOVER};
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 14px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_ACTIVE};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.collapse_btn)

        layout.addWidget(header)

        # Scroll area for nav items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                width: 4px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BG_ACTIVE};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        nav_container = QWidget()
        nav_container.setStyleSheet("background-color: transparent;")
        self.nav_layout = QVBoxLayout(nav_container)
        self.nav_layout.setContentsMargins(0, 8, 0, 8)
        self.nav_layout.setSpacing(2)

        # Navigation items
        self.buttons: list[SidebarButton] = []
        nav_items = [
            (0, "📊", "Dashboard", "Ctrl+D"),
            (1, "🔑", "Licenses", "Ctrl+L"),
            (2, "👥", "Customers", "Ctrl+C"),
            (3, "📦", "Products", "Ctrl+P"),
            (4, "📋", "Subscriptions", "Ctrl+S"),
            (5, "💻", "Machines", "Ctrl+M"),
            (6, "✅", "Activations", "Ctrl+A"),
            (7, "🔌", "Software", "Ctrl+W"),
            (8, "📥", "SDK Generator", "Ctrl+G"),
            (9, "📊", "Analytics", "Ctrl+Y"),
            (10, "📝", "Audit Logs", "Ctrl+O"),
            (11, "⚙️", "Settings", "Ctrl+,"),
        ]

        for page_index, icon, text, shortcut in nav_items:
            btn = SidebarButton(text, icon, shortcut)
            btn.clicked.connect(lambda checked, idx=page_index: self.page_changed.emit(idx))
            self.nav_layout.addWidget(btn)
            self.buttons.append(btn)

        self.nav_layout.addStretch()

        scroll.setWidget(nav_container)
        layout.addWidget(scroll, 1)

        # Bottom status
        bottom = QFrame()
        bottom.setStyleSheet(f"background-color: {Colors.BG_LIGHT}; border-top: 1px solid {Colors.BORDER_LIGHT};")
        bottom.setFixedHeight(48)
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 0, 16, 0)

        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 10px;")
        bottom_layout.addWidget(status_dot)

        self.status_text = QLabel("Connected")
        self.status_text.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px;")
        bottom_layout.addWidget(self.status_text, 1)

        self.version_label = QLabel(f"v{settings.APP_VERSION}")
        self.version_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        bottom_layout.addWidget(self.version_label)

        layout.addWidget(bottom)

    def _toggle_collapse(self) -> None:
        """Animate sidebar collapse/expand."""
        self._expanded = not self._expanded
        target_width = self._expanded_width if self._expanded else self._collapsed_width

        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.finished.connect(self._on_animation_end)
        self.animation.start()

        self.animation2 = QPropertyAnimation(self, b"minimumWidth")
        self.animation2.setDuration(200)
        self.animation2.setStartValue(self.width())
        self.animation2.setEndValue(target_width)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation2.start()

        # Update button states
        collapsed = not self._expanded
        for btn in self.buttons:
            btn.set_collapsed(collapsed)

        self.title_label.setVisible(self._expanded)
        self.collapse_btn.setText("▶" if not self._expanded else "◀")
        self.logo_label.setVisible(True)

    def _on_animation_end(self) -> None:
        """Handle animation completion."""
        pass

    def set_active_page(self, page_index: int) -> None:
        """Highlight the active page button."""
        for i, btn in enumerate(self.buttons):
            btn.set_active(i == page_index)


# ─── Top Header ──────────────────────────────────────────────────────────────

class TopHeader(QFrame):
    """Top header bar with search, notifications, theme toggle, and window controls."""

    theme_toggled = Signal()
    search_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dark_mode = True
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFixedHeight(64)
        self.setStyleSheet(f"""
            TopHeader {{
                background-color: {Colors.BG_LIGHT};
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # App icon + name
        app_icon = QLabel("🔐")
        app_icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(app_icon)

        app_name = QLabel("License Manager")
        app_name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 18px; font-weight: 700;")
        layout.addWidget(app_name)

        # Current user
        user_avatar = AvatarWidget("Admin User", size=32, color=Colors.PRIMARY)
        layout.addWidget(user_avatar)

        user_name = QLabel("Admin")
        user_name.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(user_name)

        layout.addSpacing(20)

        # Search bar
        self.search = SearchBar("Search licenses, customers, products...")
        self.search.setFixedWidth(320)
        self.search.search_submitted.connect(self.search_requested.emit)
        layout.addWidget(self.search)

        layout.addStretch()

        # Notification icon
        notif_btn = QPushButton("🔔")
        notif_btn.setFixedSize(36, 36)
        notif_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 18px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """)
        notif_btn.setToolTip("Notifications")
        layout.addWidget(notif_btn)

        # Settings icon
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(36, 36)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 18px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        # Theme toggle
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 18px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """)
        self.theme_btn.setToolTip("Toggle Theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # Server status indicator
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(76, 175, 80, 0.1);
                border: 1px solid {Colors.SUCCESS}44;
                border-radius: 16px;
                padding: 4px 12px;
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 4, 8, 4)
        status_layout.setSpacing(4)
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 10px;")
        status_layout.addWidget(status_dot)
        status_text = QLabel("Online")
        status_text.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 12px; font-weight: 600;")
        status_layout.addWidget(status_text)
        layout.addWidget(status_frame)

        # Window controls
        layout.addSpacing(8)
        controls = QHBoxLayout()
        controls.setSpacing(4)

        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(36, 28)
        minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_SECONDARY};
                border: none; border-radius: 4px; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {Colors.BG_HOVER}; }}
        """)
        minimize_btn.clicked.connect(lambda: self.window().showMinimized())
        controls.addWidget(minimize_btn)

        maximize_btn = QPushButton("□")
        maximize_btn.setFixedSize(36, 28)
        maximize_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_SECONDARY};
                border: none; border-radius: 4px; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {Colors.BG_HOVER}; }}
        """)
        maximize_btn.clicked.connect(lambda: self.window().showMaximized() if self.window().isMaximized() else self.window().showNormal())
        controls.addWidget(maximize_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_SECONDARY};
                border: none; border-radius: 4px; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {Colors.DANGER}; color: white; }}
        """)
        close_btn.clicked.connect(lambda: self.window().close())
        controls.addWidget(close_btn)

        layout.addLayout(controls)

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        self.theme_btn.setText("☀️" if not self._dark_mode else "🌙")
        self.theme_toggled.emit()

    def _open_settings(self) -> None:
        """Navigate to settings page."""
        main_window = self.window()
        if hasattr(main_window, 'sidebar') and hasattr(main_window, 'stack'):
            settings_idx = 11  # Settings is index 11
            main_window.sidebar.set_active_page(settings_idx)
            main_window.stack.setCurrentIndex(settings_idx)


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Enterprise License Manager main window."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        self.setMinimumSize(Constants.WINDOW_MIN_WIDTH, Constants.WINDOW_MIN_HEIGHT)
        self.resize(Constants.WINDOW_DEFAULT_WIDTH, Constants.WINDOW_DEFAULT_HEIGHT)

        # Apply dark theme
        self._apply_dark_theme()

        # Toast manager
        self.toast_manager = ToastManager(self)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top header
        self.header = TopHeader()
        self.header.search_requested.connect(self._on_global_search)
        self.header.theme_toggled.connect(self._toggle_theme)
        main_layout.addWidget(self.header)

        # Content area
        content_container = QWidget()
        content_container.setStyleSheet(f"background-color: {Colors.BG_MEDIUM};")
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        content_layout.addWidget(self.sidebar)

        # Stacked widget for pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {Colors.BG_MEDIUM};")
        content_layout.addWidget(self.stack, 1)

        main_layout.addWidget(content_container, 1)

        # Setup all pages
        self._setup_pages()

        # Show dashboard by default
        self.sidebar.set_active_page(0)
        self.stack.setCurrentIndex(0)

        # Show welcome toast
        QTimer.singleShot(500, self._show_welcome)

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        logger.info(f"Main window initialized - {settings.APP_NAME} v{settings.APP_VERSION}")

    def _setup_pages(self) -> None:
        """Setup all application pages and add them to the stack."""
        # SoftwarePage instances with signal connections
        self.software_page = SoftwarePage()
        self.software_page.product_added.connect(self._on_product_added)
        self.software_page.product_updated.connect(self._on_product_updated)
        self.software_page.product_deleted.connect(self._on_product_deleted)
        self.software_page.search_requested.connect(self._on_software_search)
        self.software_page.sdk_generate_requested.connect(self._on_sdk_generate)
        
        pages = [
            (DashboardPage(), "Dashboard"),
            (LicensePage(), "Licenses"),
            (CustomerPage(), "Customers"),
            (SoftwarePage(), "Products"),
            (SubscriptionPage(), "Subscriptions"),
            (MachinePage(), "Machines"),
            (ActivationPage(), "Activations"),
            (self.software_page, "Software"),
            (SdkPage(), "SDK Generator"),
            (AnalyticsPage(), "Analytics"),
            (AuditPage(), "Audit Logs"),
            (SettingsPage(), "Settings"),
        ]

        for page, name in pages:
            self.stack.addWidget(page)

        # Load software products after setup
        QTimer.singleShot(500, self._load_software_products)

        logger.info(f"Setup {len(pages)} application pages")

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for navigation."""
        from PySide6.QtGui import QShortcut, QKeySequence

        shortcuts = {
            "Ctrl+D": 0,  # Dashboard
            "Ctrl+L": 1,  # Licenses
            "Ctrl+C": 2,  # Customers
            "Ctrl+P": 3,  # Products
            "Ctrl+S": 4,  # Subscriptions
            "Ctrl+M": 5,  # Machines
            "Ctrl+A": 6,  # Activations
            "Ctrl+W": 7,  # Software
            "Ctrl+G": 8,  # SDK Generator
            "Ctrl+Y": 9,  # Analytics
            "Ctrl+O": 10, # Audit Logs
            "Ctrl+,": 11, # Settings
        }

        for key_seq, page_idx in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key_seq), self)
            shortcut.activated.connect(lambda idx=page_idx: self._navigate_to(idx))

    def _navigate_to(self, page_index: int) -> None:
        """Navigate to a specific page by index."""
        if 0 <= page_index < self.stack.count():
            self.sidebar.set_active_page(page_index)
            self.stack.setCurrentIndex(page_index)

    def _on_page_changed(self, page_index: int) -> None:
        """Handle page change from sidebar."""
        if 0 <= page_index < self.stack.count():
            self.sidebar.set_active_page(page_index)
            self.stack.setCurrentIndex(page_index)
            logger.info(f"Navigated to page: {page_index}")

    def _on_global_search(self, query: str) -> None:
        """Handle global search from the header."""
        if query.strip():
            logger.info(f"Global search: {query}")

    def _toggle_theme(self) -> None:
        """Toggle between dark and light theme."""
        self._dark_mode = not getattr(self, '_dark_mode', True)
        if self._dark_mode:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

    def _apply_dark_theme(self) -> None:
        """Apply dark theme palette."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(Colors.BG_MEDIUM))
        palette.setColor(QPalette.WindowText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.Base, QColor(Colors.BG_DARK))
        palette.setColor(QPalette.AlternateBase, QColor(Colors.BG_LIGHT))
        palette.setColor(QPalette.ToolTipBase, QColor(Colors.BG_LIGHT))
        palette.setColor(QPalette.ToolTipText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.Text, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.Button, QColor(Colors.BG_LIGHT))
        palette.setColor(QPalette.ButtonText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.BrightText, QColor(Colors.DANGER))
        palette.setColor(QPalette.Link, QColor(Colors.PRIMARY))
        palette.setColor(QPalette.Highlight, QColor(Colors.PRIMARY))
        palette.setColor(QPalette.HighlightedText, QColor(Colors.TEXT_PRIMARY))
        self.setPalette(palette)
        self._dark_mode = True

    def _apply_light_theme(self) -> None:
        """Apply light theme palette."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#F5F5F5"))
        palette.setColor(QPalette.WindowText, QColor("#212121"))
        palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.AlternateBase, QColor("#E0E0E0"))
        palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
        palette.setColor(QPalette.ToolTipText, QColor("#212121"))
        palette.setColor(QPalette.Text, QColor("#212121"))
        palette.setColor(QPalette.Button, QColor("#E0E0E0"))
        palette.setColor(QPalette.ButtonText, QColor("#212121"))
        palette.setColor(QPalette.BrightText, QColor("#D32F2F"))
        palette.setColor(QPalette.Link, QColor("#1976D2"))
        palette.setColor(QPalette.Highlight, QColor("#1976D2"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(palette)
        self._dark_mode = False

    def _show_welcome(self) -> None:
        """Show welcome toast notification."""
        self.toast_manager.show_toast(
            f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}",
            ToastType.SUCCESS
        )

    def _load_software_products(self) -> None:
        """Load software products into the Software page."""
        try:
            import asyncio
            from database import async_session_factory
            from services.software_product.service import SoftwareProductService
            from services.encryption.service import EncryptionService

            async def _load():
                async with async_session_factory() as session:
                    encryption = EncryptionService()
                    service = SoftwareProductService(session, encryption)
                    products = await service.list_products(limit=1000)
                    return [await service.to_dict(p) for p in products]

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                products = loop.run_until_complete(_load())
                self.software_page.load_products(products)
            finally:
                loop.close()

            logger.info(f"Loaded {len(products)} software products")
        except Exception as e:
            logger.warning(f"Could not load software products: {e}")
            self.software_page.load_products([])

    def _on_product_added(self, data: dict) -> None:
        """Handle adding a new software product."""
        import asyncio
        from database import async_session_factory
        from services.software_product.service import SoftwareProductService
        from services.encryption.service import EncryptionService

        async def _add():
            async with async_session_factory() as session:
                encryption = EncryptionService()
                service = SoftwareProductService(session, encryption)
                product = await service.create_product(
                    name=data["name"],
                    version=data["version"],
                    validation_type=data["validation_type"],
                    exe_name=data.get("exe_name"),
                    company_name=data.get("company_name"),
                    machine_lock=data.get("machine_lock", True),
                    max_activations=data.get("max_activations", 5),
                    anti_tamper=data.get("anti_tamper", True),
                    clock_protection=data.get("clock_protection", True),
                    feature_flags=data.get("feature_flags"),
                )
                await session.commit()
                return await service.to_dict(product)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            product = loop.run_until_complete(_add())
            self._load_software_products()
            self.software_page.show_success(f"Product '{product['name']}' registered successfully!")
        except ValueError as e:
            self.software_page.show_error(str(e))
        except Exception as e:
            self.software_page.show_error(f"Failed to add product: {e}")
        finally:
            loop.close()

    def _on_product_updated(self, data: dict) -> None:
        """Handle updating a software product."""
        import asyncio
        from database import async_session_factory
        from services.software_product.service import SoftwareProductService
        from services.encryption.service import EncryptionService

        async def _update():
            async with async_session_factory() as session:
                encryption = EncryptionService()
                service = SoftwareProductService(session, encryption)
                product_id = data.pop("product_id")
                product = await service.update_product(product_id, **data)
                await session.commit()
                return product

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_update())
            self._load_software_products()
            self.software_page.show_success("Product updated successfully!")
        except Exception as e:
            self.software_page.show_error(f"Failed to update product: {e}")
        finally:
            loop.close()

    def _on_product_deleted(self, product_id: str) -> None:
        """Handle deleting a software product."""
        import asyncio
        from database import async_session_factory
        from services.software_product.service import SoftwareProductService
        from services.encryption.service import EncryptionService

        async def _delete():
            async with async_session_factory() as session:
                encryption = EncryptionService()
                service = SoftwareProductService(session, encryption)
                result = await service.delete_product(product_id)
                await session.commit()
                return result

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_delete())
            self._load_software_products()
            self.software_page.show_success("Product deleted successfully!")
        except Exception as e:
            self.software_page.show_error(f"Failed to delete product: {e}")
        finally:
            loop.close()

    def _on_software_search(self, search_term: str) -> None:
        """Handle search in software products."""
        if not search_term.strip():
            self._load_software_products()
            return

        import asyncio
        from database import async_session_factory
        from services.software_product.service import SoftwareProductService
        from services.encryption.service import EncryptionService

        async def _search():
            async with async_session_factory() as session:
                encryption = EncryptionService()
                service = SoftwareProductService(session, encryption)
                products = await service.search_products(search_term, limit=1000)
                return [await service.to_dict(p) for p in products]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            products = loop.run_until_complete(_search())
            self.software_page.load_products(products)
        except Exception as e:
            logger.warning(f"Search failed: {e}")
        finally:
            loop.close()

    def _on_sdk_generate(self, product_id: str) -> None:
        """Handle SDK generation for a product."""
        import asyncio
        from database import async_session_factory
        from services.software_product.service import SoftwareProductService
        from services.encryption.service import EncryptionService

        async def _generate():
            async with async_session_factory() as session:
                encryption = EncryptionService()
                service = SoftwareProductService(session, encryption)
                zip_path = await service.generate_client_sdk(product_id)
                return zip_path

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            zip_path = loop.run_until_complete(_generate())
            self.software_page.show_sdk_result(zip_path)
        except Exception as e:
            self.software_page.show_error(f"SDK generation failed: {e}")
        finally:
            loop.close()

    def resizeEvent(self, event) -> None:
        """Handle window resize."""
        super().resizeEvent(event)
        if hasattr(self, 'toast_manager'):
            self.toast_manager._reposition_toasts()
