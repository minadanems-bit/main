# =====================================================
# ROLE SERVICE
# Handles role permissions and report type per role
# =====================================================

import streamlit as st

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
# Optional dynamic constants loader
# =====================================================
try:
    from constants import ROLE_MODERATOR
except Exception:
    ROLE_MODERATOR = "moderator"

try:
    from constants import ROLE_TASK_ACCESS
except Exception:
    ROLE_TASK_ACCESS = {}

try:
    from constants import ROLE_LABELS
except Exception:
    ROLE_LABELS = {}

try:
    from constants import TASK_OPENING
except Exception:
    TASK_OPENING = "opening"

try:
    from constants import TASK_CLOSING
except Exception:
    TASK_CLOSING = "closing"

try:
    from constants import TASK_INTERACTION
except Exception:
    TASK_INTERACTION = "interaction"

try:
    from constants import TASK_SOCIAL
except Exception:
    TASK_SOCIAL = "social"

try:
    from constants import TASK_CLEANING
except Exception:
    TASK_CLEANING = "cleaning"

try:
    from constants import TASK_DESIGN
except Exception:
    TASK_DESIGN = "design"


# =====================================================
# Internal helper
# =====================================================
def get_current_role_from_session() -> str | None:
    return st.session_state.get("role")


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
        "moderator": ROLE_MODERATOR,
        "mod": ROLE_MODERATOR,
        "content_moderator": ROLE_MODERATOR,
        "content moderator": ROLE_MODERATOR,
    }

    if role in legacy_map:
        return legacy_map[role]

    if role:
        return role

    return ROLE_EMPLOYEE


def get_normalized_current_role() -> str:
    return normalize_role(get_current_role_from_session())


def get_role_display_name(role_value: str | None) -> str:
    normalized = normalize_role(role_value)

    if normalized in ROLE_LABELS:
        return ROLE_LABELS[normalized]

    return normalized.replace("_", " ").title()


# =====================================================
# Dynamic permissions from constants
# =====================================================
def get_role_task_access_map() -> dict[str, list[str]]:
    dynamic_map = {}

    for role_key, tasks in (ROLE_TASK_ACCESS or {}).items():
        normalized_role = normalize_role(role_key)
        dynamic_map[normalized_role] = list(tasks or [])

    fallback_map = {
        ROLE_ADMIN: [
            TASK_OPENING,
            TASK_CLOSING,
            TASK_INTERACTION,
            TASK_SOCIAL,
            TASK_CLEANING,
            TASK_DESIGN,
            "report",
        ],
        ROLE_MANAGER: [
            TASK_OPENING,
            TASK_CLOSING,
            TASK_INTERACTION,
            TASK_SOCIAL,
            "report",
        ],
        ROLE_ACCOUNTS: [
            TASK_OPENING,
            TASK_CLOSING,
            "report",
        ],
        ROLE_EMPLOYEE: [
            TASK_OPENING,
            TASK_CLOSING,
            TASK_INTERACTION,
            TASK_SOCIAL,
            "report",
        ],
        ROLE_HR: [
            TASK_INTERACTION,
            "report",
        ],
        ROLE_CLEANER: [
            TASK_CLEANING,
            "report",
        ],
        ROLE_GRAPHIC_DESIGNER: [
            TASK_DESIGN,
            TASK_SOCIAL,
            "report",
        ],
        ROLE_MODERATOR: [
            TASK_INTERACTION,
            TASK_SOCIAL,
            "report",
        ],
    }

    for role_key, tasks in fallback_map.items():
        dynamic_map.setdefault(role_key, tasks)

    normalized_final = {}
    for role_key, tasks in dynamic_map.items():
        cleaned = []
        seen = set()

        for task_name in tasks:
            task_value = str(task_name or "").strip().lower()
            if not task_value:
                continue
            if task_value == "tasks":
                continue
            if task_value not in seen:
                seen.add(task_value)
                cleaned.append(task_value)

        if "report" not in cleaned:
            cleaned.append("report")

        normalized_final[role_key] = cleaned

    return normalized_final


# =====================================================
# Tabs per role
# =====================================================
ROLE_ALLOWED_TABS = get_role_task_access_map()


def get_allowed_tabs() -> list[str]:
    role = get_normalized_current_role()
    return ROLE_ALLOWED_TABS.get(role, ["report"])


def can_access(tab_name: str) -> bool:
    return str(tab_name or "").strip().lower() in get_allowed_tabs()


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
    ROLE_MODERATOR: "moderator",
}


def get_report_type() -> str:
    role = get_normalized_current_role()
    return ROLE_REPORT_TYPE.get(role, "operations")


# =====================================================
# Work access / block helpers
# =====================================================
def can_access_daily_operations() -> bool:
    allowed_tabs = get_allowed_tabs()
    return len(allowed_tabs) > 0


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

    if role == ROLE_GRAPHIC_DESIGNER:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط أقسام التصميم/السوشيال والتقرير."
        )

    if role == ROLE_MODERATOR:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط الأقسام المسموح بها للموديراتور والتقرير."
        )

    return "⛔ هذا الحساب غير مسموح له بدخول التشغيل اليومي حاليًا."


# =====================================================
# Report section helpers
# =====================================================
def can_include_cleaning_tasks_in_report() -> bool:
    return TASK_CLEANING in get_allowed_tabs()


def can_include_design_tasks_in_report() -> bool:
    return TASK_DESIGN in get_allowed_tabs()


def can_include_opening_tasks_in_report() -> bool:
    return TASK_OPENING in get_allowed_tabs()


def can_include_closing_tasks_in_report() -> bool:
    return TASK_CLOSING in get_allowed_tabs()


def can_include_interaction_tasks_in_report() -> bool:
    return TASK_INTERACTION in get_allowed_tabs()


def can_include_social_tasks_in_report() -> bool:
    return TASK_SOCIAL in get_allowed_tabs()


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


def is_moderator_role() -> bool:
    return get_normalized_current_role() == ROLE_MODERATOR


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
    return can_access_daily_operations() and not can_view_full_daily_operations()
