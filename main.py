#!/usr/bin/env python3
"""
Software License Manager - Main Entry Point

This is the main entry point for the Software License Manager application.
It provides options to run:
1. API Server (FastAPI backend)
2. Desktop GUI (PySide6)
3. CLI mode for batch operations

Usage:
    python main.py api        # Start the API server
    python main.py gui        # Start the desktop GUI (requires PySide6)
    python main.py --help     # Show help
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.config import settings
from core.logger import get_logger, setup_logger

logger = get_logger(__name__)


def run_api_server() -> None:
    """
    Start the FastAPI license server.

    Uses uvicorn with the configured host and port settings.
    """
    try:
        import uvicorn

        logger.info(
            "Starting API server on {host}:{port}",
            host=settings.API_HOST,
            port=settings.API_PORT,
        )

        uvicorn.run(
            "api.server.app:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.is_development,
            workers=settings.API_WORKERS,
            log_level=settings.LOG_LEVEL.lower(),
        )
    except ImportError:
        logger.error(
            "uvicorn is not installed. Install it with: pip install uvicorn"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)


def run_gui() -> None:
    """
    Start the PySide6 desktop GUI application.

    Launches the main window with the full license management interface.
    """
    try:
        from PySide6.QtWidgets import QApplication
        from app.main_window import MainWindow

        logger.info("Starting desktop GUI application")

        app = QApplication(sys.argv)
        app.setApplicationName(settings.APP_NAME)
        app.setApplicationVersion(settings.APP_VERSION)

        window = MainWindow()
        window.show()

        sys.exit(app.exec())
    except ImportError:
        logger.error(
            "PySide6 is not installed. Install it with: pip install PySide6"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start GUI: {e}")
        sys.exit(1)


def run_cli() -> None:
    """
    Run CLI commands for batch operations.

    Provides command-line license generation and management.
    """
    import asyncio
    from database import init_database, async_session_factory
    from services.encryption.service import EncryptionService
    from services.hardware.service import HardwareService
    from services.licensing.service import LicensingService

    async def generate_license_cli(args: argparse.Namespace) -> None:
        """CLI license generation."""
        from core.constants import LicenseType

        await init_database()
        async with async_session_factory() as session:
            encryption = EncryptionService()
            hardware = HardwareService()
            service = LicensingService(session, encryption, hardware)

            license_data = await service.generate_license(
                license_type=LicenseType(args.type),
                customer_id=args.customer_id,
                product_id=args.product_id,
                customer_name=args.customer_name,
                customer_email=args.customer_email,
            )

            print(f"\n✅ License Generated Successfully!")
            print(f"   License Key: {license_data['license_key']}")
            print(f"   Type: {license_data['license_type']}")
            print(f"   Customer: {license_data['customer_name']}")
            print(f"   Expires: {license_data.get('expires_at', 'Never')}")

    async def validate_license_cli(args: argparse.Namespace) -> None:
        """CLI license validation."""
        await init_database()
        async with async_session_factory() as session:
            encryption = EncryptionService()
            hardware = HardwareService()
            service = LicensingService(session, encryption, hardware)

            result = await service.validate_license(args.license_key)

            if result["valid"]:
                print(f"\n✅ License is VALID")
            else:
                print(f"\n❌ License is INVALID: {result['message']}")

    async def generate_request_cli(args: argparse.Namespace) -> None:
        """CLI machine request file generation."""
        encryption = EncryptionService()
        hardware = HardwareService()
        service = LicensingService(None, encryption, hardware)  # type: ignore

        path = service.generate_machine_request_file(args.output)
        print(f"\n✅ Machine request file generated: {path}")

    parser = argparse.ArgumentParser(description="License Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate license
    gen_parser = subparsers.add_parser("generate", help="Generate a license")
    gen_parser.add_argument("--type", required=True, help="License type")
    gen_parser.add_argument("--customer-id", required=True)
    gen_parser.add_argument("--product-id", required=True)
    gen_parser.add_argument("--customer-name", required=True)
    gen_parser.add_argument("--customer-email", required=True)
    gen_parser.set_defaults(func=generate_license_cli)

    # Validate license
    val_parser = subparsers.add_parser("validate", help="Validate a license")
    val_parser.add_argument("license_key", help="License key to validate")
    val_parser.set_defaults(func=validate_license_cli)

    # Generate machine request
    req_parser = subparsers.add_parser("request", help="Generate machine request file")
    req_parser.add_argument("--output", default="machine.request")
    req_parser.set_defaults(func=generate_request_cli)

    args = parser.parse_args(sys.argv[2:])
    if hasattr(args, "func"):
        asyncio.run(args.func(args))
    else:
        parser.print_help()


def main() -> None:
    """Main entry point for the Software License Manager."""
    parser = argparse.ArgumentParser(
        description="Software License Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py api              Start the API server
  python main.py gui              Start the desktop GUI
  python main.py cli generate --type trial --customer-id <id> --product-id <id> --customer-name "John" --customer-email "john@example.com"
  python main.py cli validate LICENSE-KEY-HERE
        """,
    )

    parser.add_argument(
        "mode",
        nargs="?",
        default="api",
        choices=["api", "gui", "cli"],
        help="Run mode (default: api)",
    )

    args = parser.parse_args(sys.argv[1:2])

    # Configure logging
    setup_logger()

    logger.info(
        "{app} v{ver} starting in {mode} mode",
        app=settings.APP_NAME,
        ver=settings.APP_VERSION,
        mode=args.mode,
    )

    if args.mode == "api":
        run_api_server()
    elif args.mode == "gui":
        run_gui()
    elif args.mode == "cli":
        run_cli()


if __name__ == "__main__":
    main()