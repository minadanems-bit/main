# =====================================================
# ROLE SERVICE
# Handles role permissions and visible modules
# =====================================================

from auth_service import get_current_role


# =====================================================
# Role → Allowed Tabs
# =====================================================
ROLE_ALLOWED_TABS = {
    "manager": [
        "opening",
        "closing",
        "interaction",
        "social",
        "report",
    ],

    "accounts": [
        "opening",
        "closing",
        "report",
    ],

    "employee": [
        "opening",
        "closing",
        "interaction",
        "social",
        "report",
    ],

    "hr": [
        "interaction",
        "report",
    ],

    "cleaner": [
        "cleaning",
        "report",
    ],

    "graphic_designer": [
        "design",
        "social",
        "report",
    ],
}


# =====================================================
# Role → Report Type
# =====================================================
ROLE_REPORT_TYPE = {
    "manager": "full",
    "accounts": "financial",
    "employee": "operations",
    "hr": "hr",
    "cleaner": "cleaning",
    "graphic_designer": "design",
}


# =====================================================
# Get allowed tabs for current user
# =====================================================
def get_allowed_tabs():
    role = get_current_role()
    return ROLE_ALLOWED_TABS.get(role, ["report"])


# =====================================================
# Get report type for current user
# =====================================================
def get_report_type():
    role = get_current_role()
    return ROLE_REPORT_TYPE.get(role, "operations")


# =====================================================
# Helper checks
# =====================================================
def can_access(tab_name: str) -> bool:
    allowed = get_allowed_tabs()
    return tab_name in allowed


def is_financial_role() -> bool:
    return get_report_type() == "financial"


def is_hr_role() -> bool:
    return get_report_type() == "hr"


def is_cleaner_role() -> bool:
    return get_report_type() == "cleaning"


def is_design_role() -> bool:
    return get_report_type() == "design"
