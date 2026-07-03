"""
Main application window for the Software License Manager desktop GUI.

Provides a modern dark-themed interface with sidebar navigation,
dashboard, and management pages for all license operations.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QApplication, QSizePolicy, QSpacerItem,
)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QAction

from core.config import settings
from core.constants import Constants
from core.logger import get_logger

from app.pages.software_page import SoftwarePage

logger = get_logger(__name__)


class SidebarButton(QPushButton):
    """Custom sidebar navigation button with hover effects."""

    def __init__(self, text: str, icon_text: str = "", parent=None) -> None:
        """Initialize sidebar button."""
        super().__init__(text, parent)
        self.icon_text = icon_text
        self.setCheckable(True)
        self.setMinimumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #B0B0B0;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3A3A3A;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #2196F3;
                color: #FFFFFF;
                font-weight: 600;
            }
        """)

    def set_active(self, active: bool) -> None:
        """Set button active state."""
        self.setChecked(active)


class Sidebar(QFrame):
    """Application sidebar with navigation items."""

    page_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        """Initialize sidebar."""
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setStyleSheet("""
            Sidebar {
                background-color: #1E1E1E;
                border-right: 1px solid #333333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # App logo/title
        title_label = QLabel("🔐 License Manager")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #FFFFFF;
            padding: 12px 8px 24px 8px;
        """)
        layout.addWidget(title_label)

        # Navigation items
        self.buttons = []
        nav_items = [
            (0, "📊", "Dashboard"),
            (1, "🔑", "Licenses"),
            (2, "📋", "Subscriptions"),
            (3, "✅", "Activation"),
            (4, "💻", "Machines"),
            (5, "👥", "Customers"),
            (6, "📦", "Products"),
            (7, "🔌", "Software"),
            (8, "⚙️", "Settings"),
            (9, "📝", "Logs"),
        ]

        for page_index, icon, text in nav_items:
            btn = SidebarButton(f"  {icon}  {text}")
            btn.clicked.connect(lambda checked, idx=page_index: self.page_changed.emit(idx))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # Version info
        version_label = QLabel(f"v{settings.APP_VERSION}")
        version_label.setStyleSheet("""
            color: #666666;
            font-size: 12px;
            padding: 8px;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

    def set_active_page(self, page_index: int) -> None:
        """Highlight the active page button."""
        for i, btn in enumerate(self.buttons):
            btn.set_active(i == page_index)


class DashboardPage(QWidget):
    """Dashboard page with statistics and status overview."""

    def __init__(self, parent=None) -> None:
        """Initialize dashboard page."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("📊 Dashboard")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(header)

        # Stats cards grid
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        stats = [
            ("🔑 Active Licenses", "0", "#4CAF50"),
            ("❌ Expired", "0", "#F44336"),
            ("📋 Subscriptions", "0", "#2196F3"),
            ("💻 Machines", "0", "#FF9800"),
        ]

        for title, value, color in stats:
            card = self._create_stat_card(title, value, color)
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        # Status section
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)

        status_header = QLabel("System Status")
        status_header.setStyleSheet("font-size: 18px; font-weight: 600; color: #FFFFFF; margin-bottom: 12px;")
        status_layout.addWidget(status_header)

        status_items = [
            ("Server Status", "✅ Online", "#4CAF50"),
            ("Last Sync", "Just now", "#B0B0B0"),
            ("API Version", settings.APP_VERSION, "#2196F3"),
            ("Database", "Connected", "#4CAF50"),
        ]

        for label, value, color in status_items:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #B0B0B0; font-size: 14px;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
            val.setAlignment(Qt.AlignRight)
            row.addWidget(lbl)
            row.addWidget(val)
            status_layout.addLayout(row)

        layout.addWidget(status_frame)
        layout.addStretch()

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a statistics card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #2D2D2D;
                border-radius: 12px;
                border-left: 4px solid {color};
                padding: 20px;
            }}
        """)
        card.setMinimumHeight(120)

        card_layout = QVBoxLayout(card)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #B0B0B0; font-size: 13px;")

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 700;")

        card_layout.addWidget(title_lbl)
        card_layout.addWidget(value_lbl)

        return card


class PlaceholderPage(QWidget):
    """Generic placeholder page for sections not yet implemented."""

    def __init__(self, title: str, emoji: str = "📄", parent=None) -> None:
        """Initialize placeholder page."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel(emoji)
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #FFFFFF; margin-top: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel("This section is under development")
        desc_label.setStyleSheet("font-size: 14px; color: #666666; margin-top: 8px;")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize main window."""
        super().__init__()

        self.setWindowTitle(settings.APP_NAME)
        self.setMinimumSize(Constants.WINDOW_MIN_WIDTH, Constants.WINDOW_MIN_HEIGHT)
        self.resize(Constants.WINDOW_DEFAULT_WIDTH, Constants.WINDOW_DEFAULT_HEIGHT)

        # Apply dark theme
        self._apply_dark_theme()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        main_layout.addWidget(self.sidebar)

        # Content area
        content_container = QWidget()
        content_container.setStyleSheet("background-color: #252526;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget for pages
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        main_layout.addWidget(content_container, 1)

        # Add pages
        self._setup_pages()

        # Show dashboard by default
        self.sidebar.set_active_page(0)
        self.stack.setCurrentIndex(0)

        logger.info("Main window initialized")

    def _setup_pages(self) -> None:
        """Setup all application pages."""
        # Software page
        self.software_page = SoftwarePage()

        # Connect software page signals
        self.software_page.product_added.connect(self._on_product_added)
        self.software_page.product_updated.connect(self._on_product_updated)
        self.software_page.product_deleted.connect(self._on_product_deleted)
        self.software_page.search_requested.connect(self._on_software_search)
        self.software_page.sdk_generate_requested.connect(self._on_sdk_generate)

        pages = [
            (DashboardPage(), "Dashboard"),
            (PlaceholderPage("License Management", "🔑"), "Licenses"),
            (PlaceholderPage("Subscriptions", "📋"), "Subscriptions"),
            (PlaceholderPage("Activation", "✅"), "Activation"),
            (PlaceholderPage("Machine Management", "💻"), "Machines"),
            (PlaceholderPage("Customer Management", "👥"), "Customers"),
            (PlaceholderPage("Product Management", "📦"), "Products"),
            (self.software_page, "Software"),
            (PlaceholderPage("Settings", "⚙️"), "Settings"),
            (PlaceholderPage("Audit Logs", "📝"), "Logs"),
        ]

        for page, name in pages:
            self.stack.addWidget(page)

        # Load software products after setup
        QTimer.singleShot(500, self._load_software_products)

    def _on_page_changed(self, page_index: int) -> None:
        """Handle page change from sidebar."""
        self.sidebar.set_active_page(page_index)
        self.stack.setCurrentIndex(page_index)
        logger.info(f"Navigated to page: {page_index}")

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

    def _apply_dark_theme(self) -> None:
        """Apply dark theme to the application."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#252526"))
        palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Base, QColor("#1E1E1E"))
        palette.setColor(QPalette.AlternateBase, QColor("#2D2D2D"))
        palette.setColor(QPalette.ToolTipBase, QColor("#2D2D2D"))
        palette.setColor(QPalette.ToolTipText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Text, QColor("#FFFFFF"))
        palette.setColor(QPalette.Button, QColor("#2D2D2D"))
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.BrightText, QColor("#FF0000"))
        palette.setColor(QPalette.Link, QColor("#2196F3"))
        palette.setColor(QPalette.Highlight, QColor("#2196F3"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))

        self.setPalette(palette)

        # Global stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252526;
            }
            QWidget {
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #616161;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)