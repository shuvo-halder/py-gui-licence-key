"""Application pages module."""

from app.pages.dashboard_page import DashboardPage
from app.pages.license_page import LicensePage
from app.pages.customer_page import CustomerPage
from app.pages.machine_page import MachinePage
from app.pages.subscription_page import SubscriptionPage
from app.pages.activation_page import ActivationPage
from app.pages.analytics_page import AnalyticsPage
from app.pages.audit_page import AuditPage
from app.pages.settings_page import SettingsPage
from app.pages.sdk_page import SdkPage
from app.pages.software_page import SoftwarePage

__all__ = [
    "DashboardPage",
    "LicensePage",
    "CustomerPage",
    "MachinePage",
    "SubscriptionPage",
    "ActivationPage",
    "AnalyticsPage",
    "AuditPage",
    "SettingsPage",
    "SdkPage",
    "SoftwarePage",
]