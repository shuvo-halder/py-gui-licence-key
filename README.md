# 🔐 Software License Manager

A **production-ready**, **enterprise-grade** desktop application for managing software licenses with cryptographic security, machine locking, subscription management, software registration, client SDK generation, and a REST API backend.

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python main.py api

# Run the desktop GUI
python main.py gui
```

---

## 🖥️ Desktop GUI (PySide6)

The application features a modern, dark-themed enterprise desktop interface built with PySide6.

### Top Header Bar
- App logo & name
- User avatar with initials
- Global search bar
- Notification & settings icons
- Dark/light theme toggle
- Server connection status indicator
- Window controls (minimize/maximize/close)

### Animated Sidebar
12 navigation items with expand/collapse animation and keyboard shortcuts:

| # | Page | Shortcut | Description |
|---|------|----------|-------------|
| 0 | 📊 Dashboard | `Ctrl+D` | SaaS-style dashboard with stats & charts |
| 1 | 🔑 Licenses | `Ctrl+L` | Full license management with CRUD |
| 2 | 👥 Customers | `Ctrl+C` | Customer directory management |
| 3 | 📦 Products | `Ctrl+P` | Software product registry |
| 4 | 📋 Subscriptions | `Ctrl+S` | Subscription plan management |
| 5 | 💻 Machines | `Ctrl+M` | Hardware/fingerprint management |
| 6 | ✅ Activations | `Ctrl+A` | License activation tracking |
| 7 | 🔌 Software | `Ctrl+W` | Registered software management |
| 8 | 📥 SDK Generator | `Ctrl+G` | Client SDK package generation |
| 9 | 📊 Analytics | `Ctrl+Y` | Charts and reporting |
| 10 | 📝 Audit Logs | `Ctrl+O` | System activity logs |
| 11 | ⚙️ Settings | `Ctrl+,` | Application configuration |

### Pages

#### Dashboard (`app/pages/dashboard_page.py`)
- 8 stat cards with icons, values, trend indicators, and mini bar charts
- 4 chart widgets: License Trend, Revenue, Subscriptions, Activations
- Recent activity feed with 7 sample activities
- Refresh and export buttons
- Loading overlay with simulated data loading

#### License Management (`app/pages/license_page.py`)
- Full table with 10 columns including checkboxes for multi-select
- Search by license key, customer, or product
- Status filter (All/Active/Inactive/Expired/Revoked) + date range
- Pagination with configurable page size (10/20/50/100)
- Action buttons: View Details, Edit, Renew, Revoke
- Create License dialog with customer/product selection, type, dates
- View License dialog with full detail info card

#### Customer Management (`app/pages/customer_page.py`)
- Searchable table with 7 columns
- Status badges for active/inactive
- Add and export actions

#### Machine Management (`app/pages/machine_page.py`)
- Hardware info: hostname, OS, CPU, RAM, fingerprint
- License binding tracking
- Activation dates and status
- Blacklist/inactive status support

#### Subscription Management (`app/pages/subscription_page.py`)
- Plans (Basic/Standard/Premium/Enterprise)
- Billing intervals (monthly/yearly/quarterly)
- Amount tracking and status badges
- Search and export

#### Activation Management (`app/pages/activation_page.py`)
- License-to-machine activation tracking
- IP address and country tracking
- Activation status management

#### Software Registration (`app/pages/software_page.py`)
- Register, edit, delete software products
- Configure validation type (online/offline/hybrid)
- Machine lock, anti-tamper, clock protection settings
- Feature flags configuration
- SDK generation per product

#### SDK Generator (`app/pages/sdk_page.py`)
- SDK generation history with version tracking
- Multiple language support (Python, JavaScript, C#, Java, Go)
- Download count and file size tracking
- Generation progress indicator with animation

#### Analytics (`app/pages/analytics_page.py`)
- 4 chart widgets: Monthly Activations, Revenue Trends, License Growth, Software Registrations
- Period filter (Daily/Weekly/Monthly/Yearly)
- Export options (PDF, CSV)

#### Audit Logs (`app/pages/audit_page.py`)
- 100+ sample audit entries with timestamps
- Severity filtering (info/warning/error/critical)
- Colored severity badges
- Search by action, user, or IP
- Pagination

#### Settings (`app/pages/settings_page.py`)
- 6-tab interface: General, Security, Database, API, Theme, Backup
- Application configuration fields
- RSA key management
- Database connection testing
- API URL and key configuration
- Dark/Light/System theme selection
- Backup & restore functionality

### UI Components (`app/widgets.py`)
- **StatCard**: Modern metrics card with icon, value, trend, mini chart
- **ToastNotification**: Auto-dismissing floating notifications (success/error/warning/info)
- **LoadingOverlay**: Full-screen loading with spinner and progress bar
- **EmptyState**: Placeholder with icon, message, and action button
- **SkeletonCard**: Loading skeleton placeholders
- **SearchBar**: Search input with icon and clear button
- **FilterBar**: Status combo + date range filters
- **Pagination**: Page navigation with configurable page size
- **StatusBadge**: Colored status indicators
- **ConfirmDialog**: Modern confirmation dialogs
- **SectionHeader**: Page header with title, subtitle, and action buttons
- **ProgressIndicator**: Determinate/indeterminate progress bars
- **InfoRow**: Key-value information display
- **ExportMenu**: Dropdown export (CSV/Excel/PDF)
- **AvatarWidget**: Circular avatar with initials
- **MiniChart**: Custom-painted mini bar charts

### Seed Data (`app/seed_data.py`)
The application includes realistic sample data for immediate demonstration:
- 12 customers with companies
- 50 license keys with various types and statuses
- 10 software products
- 24 subscriptions
- 12 machines with hardware specs
- 40 activations with IP tracking
- 14 SDK history entries
- 100 audit logs

---

## 🏗️ Architecture

```
software-license-manager/
├── app/                    # PySide6 Desktop GUI
│   ├── main_window.py     # Main window with header, sidebar, pages
│   ├── widgets.py         # 20+ reusable UI components
│   ├── seed_data.py       # Sample data for demonstration
│   └── pages/             # 12 application pages
│       ├── dashboard_page.py
│       ├── license_page.py
│       ├── customer_page.py
│       ├── machine_page.py
│       ├── subscription_page.py
│       ├── activation_page.py
│       ├── analytics_page.py
│       ├── audit_page.py
│       ├── settings_page.py
│       ├── sdk_page.py
│       └── software_page.py
├── core/                  # Core configuration
│   ├── config.py          # Pydantic Settings
│   ├── constants.py       # Enums & constants
│   └── logger.py          # Loguru logging
├── database/              # Data layer
│   ├── models/            # SQLAlchemy ORM models
│   └── repository/        # Repository pattern
├── services/              # Business logic
│   ├── encryption/        # RSA-4096, AES-256, SHA-256
│   ├── licensing/         # License generation & validation
│   ├── activation/        # Online/offline activation
│   ├── subscription/      # Subscription management
│   ├── hardware/          # Machine fingerprinting
│   └── software_product/  # Software registration & SDK generation
├── api/                   # FastAPI backend
│   └── server/            # REST API endpoints (incl. client SDK routes)
├── tests/                 # Test suite (20+ software product tests)
├── main.py                # Entry point (api/gui/cli)
├── pytest.ini             # Pytest configuration
└── requirements.txt       # Dependencies
```

---

## ✨ Features

### 🔑 License Management
- **5 License Types**: Trial, Lifetime, Monthly, Yearly, Enterprise
- **Cryptographic Signing**: RSA-4096 digital signatures
- **License Key Generation**: Cryptographically secure random keys
- **Feature-Based Licensing**: Enable/disable modules per license
- **Custom Duration**: Override default expiration periods

### ✅ Activation System
- **Online Activation**: Real-time server verification
- **Offline Activation**: File-based activation for air-gapped systems
- **Machine Request Files**: Generate `.request` files for offline activation
- **Activation Files**: Import `.lic` activation files

### 💻 Machine Locking
- **Hardware Fingerprinting**: CPU, motherboard, BIOS, disk, MAC, GUID
- **SHA-256 Hashing**: Secure, reproducible machine identifiers
- **Multi-Machine Support**: Register multiple devices per license
- **Blacklisting**: Block compromised machines

### 📋 Subscription Management
- **4 Intervals**: Monthly, Quarterly, Yearly, Enterprise
- **Auto-Renewal**: Automatic subscription renewal
- **Grace Period**: Configurable grace period after expiry
- **Status Tracking**: Active, Expired, Cancelled, Suspended, Grace Period

### 🛡️ Security
- **RSA-4096**: Asymmetric encryption for digital signatures
- **AES-256**: Symmetric encryption for local license files
- **SHA-256**: Hashing for integrity verification
- **HMAC**: Message authentication codes
- **Anti-Tampering**: Detect modified licenses and executables
- **Clock Manipulation Detection**: Prevent time-based exploits
- **JWT Authentication**: Secure API access

### 🔌 Software Registration & License Injection
- **Software Product Registry**: Register and manage software applications
- **App ID Generation**: Auto-generated UUIDs for each registered app
- **Validation Modes**: Online, Offline, and Hybrid license validation
- **Machine Locking**: Per-software machine lock configuration
- **Anti-Tamper**: Executable integrity validation per product
- **Clock Protection**: Clock manipulation detection per product
- **Feature Flags**: JSON-based feature flag configuration
- **Search & Filter**: Search registered apps by name, company, or app ID

### 📦 Client SDK Generation
- **Auto-Generated SDK**: One-click client integration package generation
- **License Client**: HTTP client for server API communication
- **License Validator**: Multi-layered startup validation (RSA, expiry, machine, anti-tamper, clock)
- **Machine Fingerprint**: Hardware-based device identification
- **Public Key Export**: RSA public key for offline signature verification
- **Config JSON**: Auto-configured SDK settings
- **README Documentation**: Auto-generated integration guide
- **ZIP Packaging**: Ready-to-distribute SDK package

### 📊 Dashboard
- 8 stat cards with trends and mini charts
- 4 chart widgets (License Trend, Revenue, Subscriptions, Activations)
- Recent activity feed
- Refresh and export functionality

### 🌐 REST API
- FastAPI backend with async support
- Full CRUD for licenses, customers, products
- Activation and validation endpoints
- Subscription management
- Machine registration
- Client SDK activation/validation endpoints
- Public key distribution

---

## 📖 Usage

### API Mode
```bash
python main.py api
```

### GUI Mode
```bash
python main.py gui
```

### CLI Mode
```bash
# Generate a trial license
python main.py cli generate \
  --type trial \
  --customer-id <uuid> \
  --product-id <uuid> \
  --customer-name "John Doe" \
  --customer-email "john@example.com"

# Validate a license
python main.py cli validate LICENSE-KEY-HERE

# Generate machine request file
python main.py cli request --output machine.request
```

---

## 🔒 Security Architecture

### Key Management
- RSA-4096 key pair generated on first run
- Private key encrypted with master secret
- AES-256 key for local file encryption
- Keys stored in `licenses/keys/` directory

### License Signing Flow
```
1. Generate license data (key, type, customer, expiry, features)
2. Create canonical JSON representation
3. Sign with RSA-4096 private key (PSS padding, SHA-256)
4. Store signature with license
5. On validation: verify with public key
```

### Client Validation Flow
```
Application Start
  ↓
Load local license file
  ↓
Verify RSA signature using public.pem
  ↓
Validate expiration date
  ↓
Validate machine fingerprint
  ↓
Check anti-tampering hash (SHA-256)
  ↓
Check clock rollback attempts
  ↓
If online/hybrid mode: POST /api/v1/client/validate
  ↓
Receive validation response
  ↓
Allow application execution (or show activation dialog)
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_software_product.py -v
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Software License Manager | Application name |
| `APP_ENV` | development | Environment (dev/staging/prod) |
| `DEBUG` | false | Debug mode |
| `SECRET_KEY` | (required) | Master encryption key |
| `DATABASE_URL` | sqlite:///./data/license_manager.db | Database connection |
| `API_HOST` | 0.0.0.0 | API server host |
| `API_PORT` | 8000 | API server port |
| `RSA_KEY_SIZE` | 4096 | RSA key size in bits |
| `LOG_LEVEL` | INFO | Logging level |

---

## 🏆 Technical Highlights

- **Clean Architecture**: Separation of concerns with layers
- **SOLID Principles**: Single responsibility, dependency injection
- **Repository Pattern**: Abstracted data access
- **Service Layer**: Business logic encapsulation
- **Type Hints**: Full type annotations throughout
- **Async/Await**: Non-blocking database and API operations
- **Comprehensive Logging**: Structured logging with Loguru
- **Security First**: Encryption, signing, anti-tampering
- **Test Coverage**: Unit and integration tests (20+ tests)
- **Reusable Widget Library**: 20+ custom PySide6 components
- **Custom Chart Engine**: Painted bar/line charts without external dependencies
- **Toast Notification System**: Auto-dismissing floating notifications
- **Keyboard Navigation**: Full keyboard shortcut support
- **Dark/Light Theme**: Toggle between dark and light themes
- **Animated UI**: Smooth sidebar collapse/expand animations
- **Seed Data**: 300+ realistic sample records for demonstration