# 🔐 Software License Manager

A **production-ready**, **enterprise-grade** desktop application for managing software licenses with cryptographic security, machine locking, subscription management, and a REST API backend.

---

## 🏗️ Architecture

```
software-license-manager/
├── app/                    # PySide6 Desktop GUI
│   ├── main_window.py     # Main window with dark theme
│   ├── pages/             # Application pages
│   ├── widgets/           # Reusable widgets
│   └── dialogs/           # Modal dialogs
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
│   └── hardware/          # Machine fingerprinting
├── api/                   # FastAPI backend
│   └── server/            # REST API endpoints
├── tests/                 # Test suite
├── main.py                # Entry point
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

### 📊 Dashboard
- Active/Expired license counts
- Subscription status overview
- Machine status indicators
- Server health monitoring
- Real-time statistics

### 🌐 REST API
- FastAPI backend with async support
- Full CRUD for licenses, customers, products
- Activation and validation endpoints
- Subscription management
- Machine registration
- Public key distribution

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/software-license-manager.git
cd software-license-manager

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the API server
python main.py api

# Or run the desktop GUI
python main.py gui
```

### Docker (API Server)

```bash
docker build -t license-manager .
docker run -p 8000:8000 license-manager
```

---

## 📖 Usage

### API Mode

Start the license server:

```bash
python main.py api
```

The API will be available at `http://localhost:8000`

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/generate-license` | Generate a new license |
| POST | `/api/v1/activate` | Activate a license online |
| POST | `/api/v1/validate` | Validate a license |
| POST | `/api/v1/renew` | Renew a subscription |
| POST | `/api/v1/revoke` | Revoke a license |
| POST | `/api/v1/machine/register` | Register a machine |
| POST | `/api/v1/machine/remove` | Remove a machine |
| POST | `/api/v1/machine/blacklist` | Blacklist a machine |
| POST | `/api/v1/subscription/create` | Create a subscription |
| POST | `/api/v1/subscription/update` | Update subscription status |
| POST | `/api/v1/subscription/cancel` | Cancel a subscription |
| POST | `/api/v1/offline-activation` | Process offline activation |
| POST | `/api/v1/license/transfer` | Transfer license to new customer |
| GET | `/api/v1/stats/licenses` | License statistics |
| GET | `/api/v1/stats/subscriptions` | Subscription statistics |
| GET | `/api/v1/public-key` | Get public key |

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

### GUI Mode

```bash
python main.py gui
```

Launches the desktop application with:
- Dark theme interface
- Sidebar navigation
- Dashboard with statistics
- License management pages
- Subscription management
- Activation tools
- Machine management
- Settings configuration

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

### Machine Locking Flow
```
1. Collect hardware identifiers (CPU, motherboard, BIOS, disk, MAC, GUID)
2. Combine and sort identifiers
3. Hash with SHA-256
4. Store fingerprint with activation
5. On validation: compare fingerprints
```

### Offline Activation Flow
```
Client:                          Server:
   |                               |
   |-- Generate machine.request -->|
   |   (encrypted with AES-256)    |
   |                               |-- Decrypt request
   |                               |-- Validate license
   |                               |-- Generate activation.lic
   |<-- Return activation.lic -----|
   |   (encrypted with AES-256)    |
   |                               |
   |-- Import activation.lic ----->|
   |   (verify signature)          |
```

---

## 🗄️ Database Schema

### Tables
- **products**: Software products with licensing policies
- **customers**: Customer information and authentication
- **licenses**: License keys, types, signatures, and status
- **subscriptions**: Recurring billing and renewal tracking
- **machines**: Registered hardware and fingerprints
- **activations**: Activation events and validation history
- **audit_logs**: Security audit trail
- **app_settings**: Application configuration

### Relationships
```
Product 1──N License
Customer 1──N License
Customer 1──N Machine
Customer 1──N Activation
License 1──1 Subscription
License 1──N Machine
License 1──N Activation
Machine 1──N Activation
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_encryption.py -v

# Run tests with verbose output
pytest -v --tb=long
```

---

## 📦 Packaging

```bash
# Package as standalone executable
pyinstaller --onefile --windowed main.py

# Package with custom icon
pyinstaller --onefile --windowed --icon=assets/icon.ico main.py
```

---

## ⚙️ Configuration

All configuration is managed through environment variables or `.env` file:

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

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

- **Documentation**: See the `docs/` directory
- **Issues**: GitHub Issues
- **Email**: support@licensemanager.com

---

## 🏆 Technical Highlights

- **Clean Architecture**: Separation of concerns with layers
- **SOLID Principles**: Single responsibility, dependency injection
- **Repository Pattern**: Abstracted data access
- **Service Layer**: Business logic encapsulation
- **Type Hints**: Full type annotations throughout
- **Async/Await**: Non-blocking database and API operations
- **Comprehensive Logging**: Structured logging with Loguru
- **Error Handling**: Graceful error recovery
- **Security First**: Encryption, signing, anti-tampering
- **Test Coverage**: Unit and integration tests