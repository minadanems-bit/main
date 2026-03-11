# =====================================================
# ROLE SERVICE
# Handles role permissions and report type per role
# =====================================================

from auth_service import get_current_role
from constants import (
    ROLE_ACCOUNTS,
    ROLE_ADMIN,
    ROLE_CLEANER,
    ROLE_EMPLOYEE,
    ROLE_GRAPHIC_DESIGNER,
    ROLE_HR,
    ROLE_MANAGER,
)


# =====================================================
# Role normalization
# =====================================================
def normalize_role(role_value: str | None) -> str:
    role = (role_value or "").strip().lower()

    legacy_map = {
        "user": ROLE_EMPLOYEE,
        "employee": ROLE_EMPLOYEE,
        "customer_service": ROLE_EMPLOYEE,
        "customer service": ROLE_EMPLOYEE,
        "customer services": ROLE_EMPLOYEE,
        "admin": ROLE_ADMIN,
        "manager": ROLE_MANAGER,
        "accounts": ROLE_ACCOUNTS,
        "accountsant": ROLE_ACCOUNTS,
        "accountant": ROLE_ACCOUNTS,
        "hr": ROLE_HR,
        "cleaner": ROLE_CLEANER,
        "office_boy": ROLE_CLEANER,
        "office boy": ROLE_CLEANER,
        "graphic_designer": ROLE_GRAPHIC_DESIGNER,
        "graphic designer": ROLE_GRAPHIC_DESIGNER,
        "designer": ROLE_GRAPHIC_DESIGNER,
    }

    return legacy_map.get(role, ROLE_EMPLOYEE)


def get_normalized_current_role() -> str:
    return normalize_role(get_current_role())


# =====================================================
# Tabs per role
# =====================================================
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


def get_allowed_tabs() -> list[str]:
    role = get_normalized_current_role()
    return ROLE_ALLOWED_TABS.get(role, ["report"])


def can_access(tab_name: str) -> bool:
    return tab_name in get_allowed_tabs()


# =====================================================
# Report type per role
# =====================================================
ROLE_REPORT_TYPE = {
    ROLE_ADMIN: "full",
    ROLE_MANAGER: "full",
    ROLE_ACCOUNTS: "financial",
    ROLE_EMPLOYEE: "customer_service",
    ROLE_HR: "hr",
    ROLE_CLEANER: "cleaning",
    ROLE_GRAPHIC_DESIGNER: "design",
}


def get_report_type() -> str:
    role = get_normalized_current_role()
    return ROLE_REPORT_TYPE.get(role, "operations")


# =====================================================
# Work access / block helpers
# =====================================================
def can_access_daily_operations() -> bool:
    role = get_normalized_current_role()
    return role in [
        ROLE_ADMIN,
        ROLE_MANAGER,
        ROLE_ACCOUNTS,
        ROLE_HR,
        ROLE_CLEANER,
        ROLE_GRAPHIC_DESIGNER,
        ROLE_EMPLOYEE,
    ]


def is_blocked_from_daily_operations() -> bool:
    return not can_access_daily_operations()


def get_daily_operations_block_message() -> str:
    role = get_normalized_current_role()

    if role == ROLE_EMPLOYEE:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط الأقسام المسموح بها حسب دوره."
        )

    if role == ROLE_CLEANER:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط قسم المهام الخاصة به والتقرير."
        )

    return "⛔ هذا الحساب غير مسموح له بدخول التشغيل اليومي حاليًا."


# =====================================================
# Report section helpers
# =====================================================
def can_include_cleaning_tasks_in_report() -> bool:
    role = get_normalized_current_role()
    return role in [ROLE_ADMIN, ROLE_CLEANER]


def can_include_design_tasks_in_report() -> bool:
    role = get_normalized_current_role()
    return role in [ROLE_ADMIN, ROLE_GRAPHIC_DESIGNER]


def can_include_opening_tasks_in_report() -> bool:
    role = get_normalized_current_role()
    return role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ACCOUNTS]


def can_include_closing_tasks_in_report() -> bool:
    role = get_normalized_current_role()
    return role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ACCOUNTS]


def can_include_interaction_tasks_in_report() -> bool:
    role = get_normalized_current_role()
    return role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_HR, ROLE_EMPLOYEE]


def can_include_social_tasks_in_report() -> bool:
    role = get_normalized_current_role()
    return role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_GRAPHIC_DESIGNER, ROLE_EMPLOYEE]


# =====================================================
# Optional helpers
# =====================================================
def is_financial_role() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ACCOUNTS]


def is_hr_role() -> bool:
    return get_normalized_current_role() == ROLE_HR


def is_cleaning_role() -> bool:
    return get_normalized_current_role() == ROLE_CLEANER


def is_design_role() -> bool:
    return get_normalized_current_role() == ROLE_GRAPHIC_DESIGNER


def is_operational_role() -> bool:
    return can_access_daily_operations()


def is_customer_service_role() -> bool:
    return get_normalized_current_role() == ROLE_EMPLOYEE


def is_manager_or_admin() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def can_access_admin_panel() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def can_access_backup_manager() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def should_use_attendance_popup() -> bool:
    return get_normalized_current_role() in [ROLE_EMPLOYEE, ROLE_CLEANER]


def can_view_full_daily_operations() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def can_view_limited_daily_operations() -> bool:
    return get_normalized_current_role() in [
        ROLE_ACCOUNTS,
        ROLE_HR,
        ROLE_CLEANER,
        ROLE_GRAPHIC_DESIGNER,
        ROLE_EMPLOYEE,
    ]
