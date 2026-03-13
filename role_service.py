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
    ROLE_MODERATOR,
    ROLE_LABELS,
    ROLE_REPORT_TYPES,
    ROLE_TASK_ACCESS,
)


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
        "accountant": ROLE_ACCOUNTS,
        "accountants": ROLE_ACCOUNTS,
        "accountsant": ROLE_ACCOUNTS,

        "hr": ROLE_HR,
        "human_resources": ROLE_HR,
        "human resources": ROLE_HR,

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
    return ROLE_LABELS.get(normalized, normalized.replace("_", " ").title())


# =====================================================
# Dynamic permissions from constants / db
# =====================================================
def _normalize_tab_name(tab_name: str | None) -> str:
    return str(tab_name or "").strip().lower()


def _clean_tabs(items: list[str] | None) -> list[str]:
    cleaned = []
    seen = set()

    for item in items or []:
        value = _normalize_tab_name(item)
        if not value:
            continue
        if value == "tasks":
            continue
        if value not in seen:
            seen.add(value)
            cleaned.append(value)

    if "report" not in seen:
        cleaned.append("report")

    return cleaned


def get_role_task_access_map(db: dict | None = None) -> dict[str, list[str]]:
    result = {}

    # 1) defaults from constants
    for role_name, tabs in (ROLE_TASK_ACCESS or {}).items():
        result[normalize_role(role_name)] = _clean_tabs(list(tabs or []))

    # 2) optional db overrides
    if db and isinstance(db.get("role_task_access"), dict):
        for role_name, tabs in db.get("role_task_access", {}).items():
            normalized_role = normalize_role(role_name)
            result[normalized_role] = _clean_tabs(list(tabs or []))

    return result


def get_role_report_type_map(db: dict | None = None) -> dict[str, str]:
    result = {}

    # 1) defaults from constants
    for role_name, report_type in (ROLE_REPORT_TYPES or {}).items():
        result[normalize_role(role_name)] = str(report_type or "").strip().lower()

    # 2) optional db overrides
    if db and isinstance(db.get("role_report_types"), dict):
        for role_name, report_type in db.get("role_report_types", {}).items():
            result[normalize_role(role_name)] = str(report_type or "").strip().lower()

    return result


# =====================================================
# Tabs per role
# =====================================================
def get_allowed_tabs(db: dict | None = None) -> list[str]:
    role = get_normalized_current_role()
    role_map = get_role_task_access_map(db)
    return role_map.get(role, ["report"])


def can_access(tab_name: str, db: dict | None = None) -> bool:
    return _normalize_tab_name(tab_name) in get_allowed_tabs(db)


# =====================================================
# Report type per role
# =====================================================
def get_report_type(db: dict | None = None) -> str:
    role = get_normalized_current_role()
    report_map = get_role_report_type_map(db)
    return report_map.get(role, "operations")


# =====================================================
# Work access / block helpers
# =====================================================
def can_access_daily_operations(db: dict | None = None) -> bool:
    allowed_tabs = get_allowed_tabs(db)
    return len(allowed_tabs) > 0


def is_blocked_from_daily_operations(db: dict | None = None) -> bool:
    return not can_access_daily_operations(db)


def get_daily_operations_block_message() -> str:
    role = get_normalized_current_role()

    if role == ROLE_EMPLOYEE:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط الأقسام المسموح بها حسب دوره."
        )

    if role == ROLE_ACCOUNTS:
        return (
            "⛔ هذا الحساب لديه صلاحيات تشغيل محدودة.\n"
            "سيظهر له فقط الأقسام المالية والتقرير والمهام المسموح بها."
        )

    if role == ROLE_HR:
        return (
            "⛔ هذا الحساب لديه صلاحيات تشغيل محدودة.\n"
            "سيظهر له فقط الأقسام الخاصة به والتقرير وما يلزمه من متابعة."
        )

    if role == ROLE_CLEANER:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط قسم المهام الخاصة به والتقرير."
        )

    if role == ROLE_GRAPHIC_DESIGNER:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط أقسام التصميم/السوشيال/التفاعل والتقرير."
        )

    if role == ROLE_MODERATOR:
        return (
            "⛔ هذا الحساب لا يملك صلاحية كاملة على كل أقسام التشغيل اليومي.\n"
            "سيظهر له فقط أقسام الموديريشن والتفاعل والسوشيال والتقرير."
        )

    return "⛔ هذا الحساب غير مسموح له بدخول التشغيل اليومي حاليًا."


# =====================================================
# Report section helpers
# =====================================================
def can_include_cleaning_tasks_in_report(db: dict | None = None) -> bool:
    return "cleaning" in get_allowed_tabs(db)


def can_include_design_tasks_in_report(db: dict | None = None) -> bool:
    return "design" in get_allowed_tabs(db)


def can_include_opening_tasks_in_report(db: dict | None = None) -> bool:
    return "opening" in get_allowed_tabs(db)


def can_include_closing_tasks_in_report(db: dict | None = None) -> bool:
    return "closing" in get_allowed_tabs(db)


def can_include_interaction_tasks_in_report(db: dict | None = None) -> bool:
    return "interaction" in get_allowed_tabs(db)


def can_include_social_tasks_in_report(db: dict | None = None) -> bool:
    return "social" in get_allowed_tabs(db)


def can_include_moderation_tasks_in_report(db: dict | None = None) -> bool:
    return "moderation" in get_allowed_tabs(db)


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


def is_operational_role(db: dict | None = None) -> bool:
    return can_access_daily_operations(db)


def is_customer_service_role() -> bool:
    return get_normalized_current_role() == ROLE_EMPLOYEE


def is_manager_or_admin() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def can_access_admin_panel() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def can_access_backup_manager() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def should_use_attendance_popup() -> bool:
    return get_normalized_current_role() in [ROLE_EMPLOYEE, ROLE_CLEANER, ROLE_MODERATOR]


def can_view_full_daily_operations() -> bool:
    return get_normalized_current_role() in [ROLE_ADMIN, ROLE_MANAGER]


def can_view_limited_daily_operations(db: dict | None = None) -> bool:
    return can_access_daily_operations(db) and not can_view_full_daily_operations()


def can_access_crm(db: dict | None = None) -> bool:
    return "crm" in get_allowed_tabs(db)
