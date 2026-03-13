# =====================================================
# ROLE MANAGEMENT SERVICE
# Dynamic roles, task access, labels, and report types
# =====================================================

from __future__ import annotations

import streamlit as st

from database import load_db, save_db


# =====================================================
# Defaults
# =====================================================
DEFAULT_ROLE_CONFIG = {
    "admin": {
        "label": "Admin",
        "task_access": ["opening", "closing", "interaction", "social", "cleaning", "design", "moderation"],
        "report_type": "full",
        "can_access_daily_operations": True,
    },
    "manager": {
        "label": "Manager",
        "task_access": ["opening", "closing", "interaction", "social", "moderation"],
        "report_type": "full",
        "can_access_daily_operations": True,
    },
    "employee": {
        "label": "Customer Service",
        "task_access": ["opening", "closing", "interaction", "social"],
        "report_type": "customer_service",
        "can_access_daily_operations": True,
    },
    "accounts": {
        "label": "Accountant",
        "task_access": ["opening", "closing"],
        "report_type": "financial",
        "can_access_daily_operations": True,
    },
    "hr": {
        "label": "HR",
        "task_access": [],
        "report_type": "hr",
        "can_access_daily_operations": False,
    },
    "cleaner": {
        "label": "Cleaner",
        "task_access": ["cleaning"],
        "report_type": "cleaning",
        "can_access_daily_operations": True,
    },
    "graphic_designer": {
        "label": "Graphic Designer",
        "task_access": ["design", "social"],
        "report_type": "design",
        "can_access_daily_operations": True,
    },
    "moderator": {
        "label": "Moderator",
        "task_access": ["moderation", "interaction", "social"],
        "report_type": "operations",
        "can_access_daily_operations": True,
    },
}

DEFAULT_TASK_CATEGORY_LABELS = {
    "opening": "Opening",
    "closing": "Closing",
    "interaction": "Interaction",
    "social": "Social",
    "cleaning": "Cleaning",
    "design": "Design",
    "moderation": "Moderation",
}


# =====================================================
# Helpers
# =====================================================
def _normalize(value: str | None) -> str:
    return str(value or "").strip().lower()


def ensure_role_management_defaults(db: dict) -> bool:
    changed = False

    if "role_definitions" not in db or not isinstance(db.get("role_definitions"), dict):
        db["role_definitions"] = dict(DEFAULT_ROLE_CONFIG)
        changed = True

    if "task_category_labels" not in db or not isinstance(db.get("task_category_labels"), dict):
        db["task_category_labels"] = dict(DEFAULT_TASK_CATEGORY_LABELS)
        changed = True

    return changed


def get_role_definitions(db: dict) -> dict:
    ensure_role_management_defaults(db)
    return db.get("role_definitions", {})


def get_task_category_labels(db: dict) -> dict:
    ensure_role_management_defaults(db)
    return db.get("task_category_labels", {})


def get_role_options(db: dict) -> list[str]:
    role_defs = get_role_definitions(db)
    return sorted(role_defs.keys())


def get_role_label(db: dict, role_name: str) -> str:
    role_defs = get_role_definitions(db)
    role_key = _normalize(role_name)

    if role_key in role_defs:
        return role_defs[role_key].get("label", role_key.replace("_", " ").title())

    return role_key.replace("_", " ").title()


def get_role_task_access(db: dict, role_name: str) -> list[str]:
    role_defs = get_role_definitions(db)
    role_key = _normalize(role_name)

    if role_key not in role_defs:
        return []

    access = role_defs[role_key].get("task_access", [])
    return [_normalize(item) for item in access if _normalize(item)]


def get_role_report_type(db: dict, role_name: str) -> str:
    role_defs = get_role_definitions(db)
    role_key = _normalize(role_name)

    if role_key not in role_defs:
        return "operations"

    return _normalize(role_defs[role_key].get("report_type", "operations")) or "operations"


def can_role_access_daily_operations(db: dict, role_name: str) -> bool:
    role_defs = get_role_definitions(db)
    role_key = _normalize(role_name)

    if role_key not in role_defs:
        return False

    return bool(role_defs[role_key].get("can_access_daily_operations", False))


# =====================================================
# CRUD
# =====================================================
def create_role(
    role_name: str,
    label: str,
    task_access: list[str],
    report_type: str = "operations",
    can_access_daily_operations: bool = True,
) -> tuple[bool, str]:
    db = load_db()
    ensure_role_management_defaults(db)

    role_key = _normalize(role_name)
    if not role_key:
        return False, "Role name is required."

    if role_key in db["role_definitions"]:
        return False, "Role already exists."

    db["role_definitions"][role_key] = {
        "label": label.strip() or role_key.replace("_", " ").title(),
        "task_access": [_normalize(item) for item in task_access if _normalize(item)],
        "report_type": _normalize(report_type) or "operations",
        "can_access_daily_operations": bool(can_access_daily_operations),
    }

    save_db(db)
    return True, "Role created successfully."


def update_role(
    role_name: str,
    label: str,
    task_access: list[str],
    report_type: str,
    can_access_daily_operations: bool,
) -> tuple[bool, str]:
    db = load_db()
    ensure_role_management_defaults(db)

    role_key = _normalize(role_name)
    if role_key not in db["role_definitions"]:
        return False, "Role not found."

    db["role_definitions"][role_key] = {
        "label": label.strip() or role_key.replace("_", " ").title(),
        "task_access": [_normalize(item) for item in task_access if _normalize(item)],
        "report_type": _normalize(report_type) or "operations",
        "can_access_daily_operations": bool(can_access_daily_operations),
    }

    save_db(db)
    return True, "Role updated successfully."


def delete_role(role_name: str) -> tuple[bool, str]:
    db = load_db()
    ensure_role_management_defaults(db)

    role_key = _normalize(role_name)
    if role_key in ["admin", "manager", "employee"]:
        return False, "Core roles cannot be deleted."

    if role_key not in db["role_definitions"]:
        return False, "Role not found."

    # حماية: لا تحذف دور مستخدم فعلي
    for _, user_data in db.get("users", {}).items():
        if _normalize(user_data.get("role")) == role_key:
            return False, "This role is assigned to one or more users."

    del db["role_definitions"][role_key]
    save_db(db)
    return True, "Role deleted successfully."


# =====================================================
# UI
# =====================================================
def role_management_ui() -> None:
    db = load_db()
    changed = ensure_role_management_defaults(db)
    if changed:
        save_db(db)
        db = load_db()

    st.title("🧩 Roles & Permissions")

    role_defs = get_role_definitions(db)
    category_labels = get_task_category_labels(db)
    task_categories = list(category_labels.keys())

    tab1, tab2 = st.tabs(["Manage Roles", "Task Categories"])

    with tab1:
        st.subheader("Create New Role")

        new_role_name = st.text_input("Role Key", key="new_role_name")
        new_role_label = st.text_input("Role Label", key="new_role_label")
        new_role_tasks = st.multiselect(
            "Allowed Task Categories",
            task_categories,
            format_func=lambda x: category_labels.get(x, x.title()),
            key="new_role_tasks",
        )
        new_role_report_type = st.text_input("Report Type", value="operations", key="new_role_report_type")
        new_role_can_ops = st.checkbox("Can access Daily Operations", value=True, key="new_role_can_ops")

        if st.button("➕ Create Role", use_container_width=True):
            success, message = create_role(
                role_name=new_role_name,
                label=new_role_label,
                task_access=new_role_tasks,
                report_type=new_role_report_type,
                can_access_daily_operations=new_role_can_ops,
            )
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        st.divider()
        st.subheader("Edit Existing Role")

        role_options = sorted(role_defs.keys())
        if not role_options:
            st.info("No roles found.")
        else:
            selected_role = st.selectbox("Select Role", role_options, key="edit_selected_role")
            role_info = role_defs.get(selected_role, {})

            edit_label = st.text_input("Role Label", value=role_info.get("label", ""), key=f"edit_label_{selected_role}")
            edit_tasks = st.multiselect(
                "Allowed Task Categories",
                task_categories,
                default=role_info.get("task_access", []),
                format_func=lambda x: category_labels.get(x, x.title()),
                key=f"edit_tasks_{selected_role}",
            )
            edit_report_type = st.text_input(
                "Report Type",
                value=role_info.get("report_type", "operations"),
                key=f"edit_report_type_{selected_role}",
            )
            edit_can_ops = st.checkbox(
                "Can access Daily Operations",
                value=bool(role_info.get("can_access_daily_operations", False)),
                key=f"edit_can_ops_{selected_role}",
            )

            c1, c2 = st.columns(2)

            with c1:
                if st.button("💾 Save Role Changes", use_container_width=True):
                    success, message = update_role(
                        role_name=selected_role,
                        label=edit_label,
                        task_access=edit_tasks,
                        report_type=edit_report_type,
                        can_access_daily_operations=edit_can_ops,
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            with c2:
                if st.button("🗑 Delete Role", use_container_width=True):
                    success, message = delete_role(selected_role)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tab2:
        st.subheader("Task Categories Labels")

        labels_map = db.get("task_category_labels", {})
        for category_name in task_categories:
            labels_map[category_name] = st.text_input(
                f"Label for {category_name}",
                value=labels_map.get(category_name, category_name.title()),
                key=f"task_label_{category_name}",
            )

        if st.button("💾 Save Category Labels", use_container_width=True):
            db["task_category_labels"] = labels_map
            save_db(db)
            st.success("Task category labels updated.")
            st.rerun()
