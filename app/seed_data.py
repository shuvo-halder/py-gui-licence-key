"""
Seed data module for providing realistic dummy data for all pages.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import Any


def _random_date(start_year: int = 2024, end_year: int = 2026) -> str:
    """Generate a random date string."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    date = start + timedelta(days=random_days)
    return date.strftime("%Y-%m-%d %H:%M:%S")


def _random_future_date() -> str:
    """Generate a future date."""
    days = random.randint(30, 365)
    date = datetime.now() + timedelta(days=days)
    return date.strftime("%Y-%m-%d %H:%M:%S")


# ── Customer Data ──────────────────────────────────────────────────────────

CUSTOMERS = [
    {"id": f"CUST-{i:04d}", "name": name, "email": email, "company": company, "status": status, "licenses": lic, "machines": mach}
    for i, (name, email, company, status, lic, mach) in enumerate([
        ("John Smith", "john@acmecorp.com", "Acme Corp", "active", 5, 3),
        ("Sarah Johnson", "sarah@globex.com", "Globex Inc", "active", 12, 8),
        ("Mike Chen", "mike@initech.com", "Initech", "active", 3, 2),
        ("Emma Wilson", "emma@umbrella.com", "Umbrella Corp", "active", 25, 15),
        ("Alex Turner", "alex@stark.com", "Stark Industries", "active", 50, 30),
        ("Lisa Anderson", "lisa@wayne.com", "Wayne Enterprises", "active", 8, 5),
        ("David Brown", "david@oscorp.com", "Oscorp", "inactive", 2, 1),
        ("Rachel Green", "rachel@cyberdyne.com", "Cyberdyne Systems", "active", 15, 10),
        ("Tom Martinez", "tom@tyrell.com", "Tyrell Corp", "active", 7, 4),
        ("Anna Lee", "anna@w.onn.com", "Wonka Industries", "active", 20, 12),
        ("Chris Davis", "chris@massive.com", "Massive Dynamic", "inactive", 4, 2),
        ("Maria Garcia", "maria@delos.com", "Delos Inc", "active", 30, 18),
    ])
]

# ── License Data ───────────────────────────────────────────────────────────

LICENSE_TYPES = ["perpetual", "subscription", "trial", "concurrent"]
LICENSE_STATUSES = ["active", "active", "active", "expired", "revoked", "pending"]

LICENSES = [
    {
        "id": f"LIC-{i:05d}",
        "key": "-".join([
            uuid.uuid4().hex[:8].upper(),
            uuid.uuid4().hex[:4].upper(),
            uuid.uuid4().hex[:4].upper(),
            uuid.uuid4().hex[:4].upper(),
            uuid.uuid4().hex[:12].upper(),
        ]),
        "customer": random.choice(CUSTOMERS)["name"],
        "product": random.choice(["OfficeSuite Pro", "DesignMaster", "DataVault", "CloudSync", "DevToolKit", "SecureShield", "AnalyticsPro", "MediaStudio"]),
        "type": random.choice(LICENSE_TYPES),
        "status": random.choice(LICENSE_STATUSES),
        "created": _random_date(2024, 2025),
        "expiry": _random_future_date(),
        "machine_count": random.randint(0, 5),
    }
    for i in range(50)
]

# ── Software Products ─────────────────────────────────────────────────────

SOFTWARE_PRODUCTS = [
    {
        "id": f"SW-{i:03d}",
        "name": name,
        "app_id": uuid.uuid4().hex[:8].upper(),
        "version": version,
        "company": company,
        "validation_type": val_type,
        "machines": random.randint(10, 500),
        "status": "active" if random.random() > 0.2 else "inactive",
        "created": _random_date(2023, 2025),
    }
    for i, (name, version, company, val_type) in enumerate([
        ("OfficeSuite Pro", "3.2.1", "Acme Software", "online"),
        ("DesignMaster", "2.0.0", "Creative Labs", "hybrid"),
        ("DataVault Enterprise", "4.5.0", "SecureData Inc", "offline"),
        ("CloudSync Manager", "1.8.3", "CloudTech Solutions", "online"),
        ("DevToolKit Pro", "5.1.0", "DevTools Inc", "hybrid"),
        ("SecureShield", "2.3.0", "CyberDefense Corp", "offline"),
        ("AnalyticsPro", "3.0.0", "DataWise Analytics", "online"),
        ("MediaStudio Suite", "6.2.1", "MediaPro Studios", "hybrid"),
        ("NetworkMonitor", "4.0.0", "NetGuard Systems", "online"),
        ("BackupAssist Pro", "2.1.0", "DataSafe Inc", "offline"),
    ])
]

# ── Subscriptions ─────────────────────────────────────────────────────────

SUBSCRIPTIONS = [
    {
        "id": f"SUB-{i:04d}",
        "customer": random.choice(CUSTOMERS)["name"],
        "product": product,
        "plan": random.choice(["Basic", "Standard", "Premium", "Enterprise"]),
        "status": random.choice(["active", "active", "active", "expired", "cancelled"]),
        "start_date": _random_date(2024, 2025),
        "end_date": _random_future_date(),
        "amount": round(random.uniform(29.99, 999.99), 2),
        "billing": random.choice(["monthly", "yearly", "quarterly"]),
    }
    for i, product in enumerate([
        "OfficeSuite Pro", "DesignMaster", "DataVault", "CloudSync",
        "DevToolKit", "SecureShield", "AnalyticsPro", "MediaStudio",
    ] * 3)
]

# ── Machines ──────────────────────────────────────────────────────────────

MACHINES = [
    {
        "id": f"MAC-{i:04d}",
        "fingerprint": uuid.uuid4().hex[:16].upper(),
        "hostname": hostname,
        "os": os,
        "cpu": cpu,
        "ram": ram,
        "license": random.choice(LICENSES)["key"],
        "activation_date": _random_date(2024, 2025),
        "status": random.choice(["active", "active", "active", "blacklisted", "inactive"]),
    }
    for i, (hostname, os, cpu, ram) in enumerate([
        ("WS-001", "Windows 11 Pro", "Intel Core i7-13700K", "32GB"),
        ("WS-002", "Windows 10 Pro", "AMD Ryzen 9 5950X", "64GB"),
        ("WS-003", "macOS Sonoma", "Apple M2 Pro", "16GB"),
        ("WS-004", "Ubuntu 22.04", "Intel Core i9-13900K", "128GB"),
        ("WS-005", "Windows 11 Pro", "Intel Core i5-13600K", "32GB"),
        ("SRV-001", "Ubuntu Server 22.04", "AMD EPYC 7742", "256GB"),
        ("SRV-002", "Debian 12", "Intel Xeon Platinum", "512GB"),
        ("LAP-001", "Windows 11 Pro", "Intel Core i7-1360P", "16GB"),
        ("LAP-002", "macOS Ventura", "Apple M1 Pro", "32GB"),
        ("LAP-003", "Windows 11 Pro", "AMD Ryzen 7 7840U", "16GB"),
        ("DEV-001", "Fedora 38", "Intel Core i9-13900K", "64GB"),
        ("DEV-002", "Arch Linux", "AMD Ryzen 9 7950X", "64GB"),
    ])
]

# ── Activations ───────────────────────────────────────────────────────────

ACTIVATIONS = [
    {
        "id": f"ACT-{i:05d}",
        "license": random.choice(LICENSES)["key"],
        "machine": random.choice(MACHINES)["fingerprint"],
        "customer": random.choice(CUSTOMERS)["name"],
        "status": random.choice(["active", "active", "active", "deactivated", "suspended"]),
        "activated_at": _random_date(2024, 2025),
        "ip_address": f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "country": random.choice(["US", "UK", "DE", "JP", "CA", "AU", "FR", "BR"]),
    }
    for i in range(40)
]

# ── SDK History ───────────────────────────────────────────────────────────

SDK_HISTORY = [
    {
        "id": f"SDK-{i:04d}",
        "software": sw,
        "version": f"1.{i}.0",
        "language": random.choice(["Python", "JavaScript", "C#", "Java", "Go"]),
        "created": _random_date(2024, 2025),
        "size": f"{round(random.uniform(0.5, 15.0), 1)} MB",
        "downloads": random.randint(10, 500),
    }
    for i, sw in enumerate([
        "OfficeSuite Pro", "DesignMaster", "DataVault", "CloudSync",
        "DevToolKit", "SecureShield", "AnalyticsPro",
    ] * 2)
]

# ── Audit Logs ────────────────────────────────────────────────────────────

AUDIT_LOGS = [
    {
        "id": f"LOG-{i:06d}",
        "timestamp": _random_date(2025, 2026),
        "action": random.choice([
            "License Generated", "License Activated", "License Revoked",
            "License Renewed", "Machine Registered", "Machine Blacklisted",
            "Software Registered", "Software Updated", "SDK Generated",
            "User Login", "User Logout", "Settings Changed",
            "Subscription Created", "Subscription Cancelled",
            "API Key Generated", "Database Backup",
        ]),
        "user": random.choice(["admin", "john.smith", "sarah.j", "mike.c", "system"]),
        "severity": random.choice(["info", "info", "info", "warning", "error", "critical"]),
        "ip": f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "details": "Action completed successfully",
    }
    for i in range(100)
]


class SeedData:
    """Provides realistic seed data for all application pages."""

    customers = CUSTOMERS
    licenses = LICENSES
    software_products = SOFTWARE_PRODUCTS
    subscriptions = SUBSCRIPTIONS
    machines = MACHINES
    activations = ACTIVATIONS
    sdk_history = SDK_HISTORY
    audit_logs = AUDIT_LOGS

    @staticmethod
    def monthly_activations() -> list[dict]:
        """Generate monthly activation data."""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return [
            {
                "month": month,
                "year": 2025,
                "activations": random.randint(50, 300),
                "deactivations": random.randint(10, 50),
                "revenue": round(random.uniform(5000, 50000), 2),
            }
            for month in months
        ]

    @staticmethod
    def revenue_trend() -> list[dict]:
        """Generate revenue trend data."""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return [
            {
                "month": month,
                "year": 2025,
                "revenue": round(random.uniform(10000, 100000), 2),
                "subscriptions": round(random.uniform(5000, 40000), 2),
                "licenses": round(random.uniform(3000, 50000), 2),
            }
            for month in months
        ]

    @staticmethod
    def dashboard_stats() -> dict[str, Any]:
        """Get dashboard statistics."""
        return {
            "total_licenses": {"value": "1,284", "trend": "+12.5%", "up": True},
            "active_licenses": {"value": "1,042", "trend": "+8.3%", "up": True},
            "expired_licenses": {"value": "156", "trend": "-3.2%", "up": False},
            "revenue": {"value": "$284,750.50", "trend": "+15.7%", "up": True},
            "active_machines": {"value": "543", "trend": "+5.1%", "up": True},
            "registered_software": {"value": "47", "trend": "+2.3%", "up": True},
            "sdk_generated": {"value": "389", "trend": "+22.4%", "up": True},
            "api_status": {"value": "Operational", "trend": "99.9% uptime", "up": True},
        }