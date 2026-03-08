# =====================================================
# ROLE SERVICE
# Handles role permissions and report type per role
# =====================================================

from auth_service import get_current_role


ROLE_MANAGER = "manager"
ROLE_EMPLOYEE = "employee"
ROLE_ACCOUNTS = "accounts"
ROLE_HR = "hr"
ROLE_CLEANER = "cleaner"
ROLE_GRAPHIC_DESIGNER = "graphic_designer"
ROLE_ADMIN = "admin"
ROLE_USER = "user"  # legacy


def normalize_role(role_value: str | None) -> str:
    role = (role_value or "").strip().lower()

    legacy_map = {
        "user": ROLE_EMPLOYEE,
        "employee": ROLE_EMPLOYEE,
        "admin": ROLE_ADMIN,
        "manager": ROLE_MANAGER,
        "accounts": ROLE_ACCOUNTS,
        "hr": ROLE_HR,
        "cleaner": ROLE_CLEANER,
        "graphic_designer": ROLE_GRAPHIC_DESIGNER,
        "graphic designer": ROLE_GRAPHIC_DESIGNER,
        "designer": ROLE_GRAPHIC_DESIGNER,
    }

    return legacy_map.get(role, ROLE_EMPLOYEE)


ROLE_ALLOWED_TABS = {
    ROLE_ADMIN: [
        "opening",
        "closing",
        "interaction",
        "social",
        "cleaning",
        "design",
        "report",
    ],
    ROLE_MANAGER: [
        "opening",
        "closing",
        "interaction",
        "social",
        "report",
    ],
    ROLE_ACCOUNTS: [
        "opening",
        "closing",
        "report",
    ],
    ROLE_EMPLOYEE: [
        "opening",
        "closing",
        "interaction",
        "social",
        "report",
    ],
    ROLE_HR: [
        "interaction",
        "report",
    ],
    ROLE_CLEANER: [
        "cleaning",
        "report",
    ],
    ROLE_GRAPHIC_DESIGNER: [
        "design",
        "social",
        "report",
    ],
}


ROLE_REPORT_TYPE = {
    ROLE_ADMIN: "full",
    ROLE_MANAGER: "full",
    ROLE_ACCOUNTS: "financial",
    ROLE_EMPLOYEE: "operations",
    ROLE_HR: "hr",
    ROLE_CLEANER: "cleaning",
    ROLE_GRAPHIC_DESIGNER: "design",
}


def get_normalized_current_role() -> str:
    return normalize_role(get_current_role())


def get_allowed_tabs() -> list[str]:
    role = get_normalized_current_role()
    return ROLE_ALLOWED_TABS.get(role, ["report"])


def get_report_type() -> str:
    role = get_normalized_current_role()
    return ROLE_REPORT_TYPE.get(role, "operations")


def can_access(tab_name: str) -> bool:
    return tab_name in get_allowed_tabs()
