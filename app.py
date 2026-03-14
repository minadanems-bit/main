import os
import json
import base64
import time
from datetime import datetime, date

import pandas as pd
import streamlit as st

from auth_service import (
    get_current_role,
    get_current_username,
    is_logged_in,
    logout_user,
    render_login_screen,
)
from constants import (
    ADMIN_MODULE_ARCHIVE,
    ADMIN_MODULE_BRANCHES,
    ADMIN_MODULE_CRM,
    ADMIN_MODULE_HR,
    ADMIN_MODULE_OPTIONS,
    ADMIN_MODULE_PAYROLL,
    ADMIN_MODULE_PRINTERS,
    ADMIN_MODULE_ROLE_MANAGEMENT,
    ADMIN_MODULE_TASKS,
    ADMIN_MODULE_TRAINING,
    HR_RECORD_KEYS,
    HR_RECORD_LABELS,
    PAYOUT_METHOD_LABELS,
    PAYROLL_ENTRY_KEY_MAP,
    ROLE_ADMIN,
    ROLE_CLEANER,
    ROLE_EMPLOYEE,
    ROLE_LABELS,
    ROLE_MANAGER,
    SESSION_USER,
    TASK_CATEGORIES,
)
from database import (
    load_db,
    load_user_draft,
    save_db,
    save_user_draft,
)
from operations_service import daily_operations_ui
from birthday_ui import birthday_ui
from printer_service import printer_management_ui
from role_service import (
    normalize_role,
    can_access_daily_operations,
    get_daily_operations_block_message,
)
from supabase_migration import migrate
from training_service import render_training_module as render_training_service_module
from ui_helpers import (
    render_attendance_clock_widget,
    render_role_dashboard_cards,
)


# =========================
# Cached DB bootstrap
# =========================
@st.cache_data(show_spinner=False, ttl=20)
def cached_load_db() -> dict:
    return load_db()


db = cached_load_db()


# =========================
# Navigation keys
# =========================
NAV_DASHBOARD = "dashboard"
NAV_PROFILE = "profile"
NAV_OPERATIONS = "operations"
NAV_ADMIN = "admin"
NAV_BACKUP = "backup"
NAV_BIRTHDAY = "birthday"

SESSION_MAIN_VIEW = "main_view"

# draft/session helpers
SESSION_DRAFTS_LOADED = "_drafts_loaded"
SESSION_LAST_DRAFT_SAVE_TS = "_last_draft_save_ts"

AUTOSAVE_INTERVAL_SECONDS = 20


# =========================
# Helpers
# =========================
def refresh_db() -> None:
    global db
    cached_load_db.clear()
    db = cached_load_db()


def persist_db_and_rerun(success_message: str | None = None) -> None:
    save_db(db)
    cached_load_db.clear()
    if success_message:
        st.success(success_message)
    st.rerun()


def ensure_db_defaults() -> None:
    defaults = {
        "users": {},
        "logs": [],
        "drafts": {},
        "tasks": {
            "opening": [],
            "closing": [],
            "social": [],
            "interaction": [],
            "cleaning": [],
            "design": [],
            "moderation": [],
        },
        "branches": [],
        "expense_categories": [],
        "history": [],
        "training_records": {},
        "printers": {},
        "attendance_records": {},
        "late_tracking": {},
        "blocked_users": {},
        "crm_records": [],
        "crm_notifications": [],
        "internal_messages": [],
        "role_definitions": {},
        "role_task_access": {},
        "role_report_types": {},
        "task_category_labels": {},
    }

    changed = False
    for key, default_value in defaults.items():
        if key not in db:
            db[key] = default_value
            changed = True

    if changed:
        save_db(db)
        cached_load_db.clear()


def ensure_ui_defaults() -> None:
    if SESSION_MAIN_VIEW not in st.session_state:
        st.session_state[SESSION_MAIN_VIEW] = NAV_DASHBOARD

    if SESSION_DRAFTS_LOADED not in st.session_state:
        st.session_state[SESSION_DRAFTS_LOADED] = False

    if SESSION_LAST_DRAFT_SAVE_TS not in st.session_state:
        st.session_state[SESSION_LAST_DRAFT_SAVE_TS] = 0.0


def get_current_user() -> dict:
    username = get_current_username()
    if not username:
        return {}
    return db.get("users", {}).get(username, {})


def safe_user_image(user_info: dict, width: int = 120) -> None:
    photo = user_info.get("photo")
    if not photo:
        st.write("👤 No Photo")
        return

    try:
        st.image(base64.b64decode(photo), width=width)
    except Exception:
        st.write("👤 Invalid Photo")


def parse_hiring_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return date(2024, 1, 1)


def get_role_label(role_value: str) -> str:
    return ROLE_LABELS.get(role_value, str(role_value).replace("_", " ").title())


def get_payout_method_label(method_value: str) -> str:
    return PAYOUT_METHOD_LABELS.get(method_value, str(method_value).replace("_", " ").title())


def get_normalized_role() -> str:
    return normalize_role(get_current_role())


def is_customer_service_role() -> bool:
    return get_normalized_role() == ROLE_EMPLOYEE


def is_cleaner_role() -> bool:
    return get_normalized_role() == ROLE_CLEANER


def is_admin_or_manager() -> bool:
    return get_normalized_role() in [ROLE_ADMIN, ROLE_MANAGER]


def can_open_admin_panel() -> bool:
    return is_admin_or_manager()


def can_open_backup_manager() -> bool:
    return is_admin_or_manager()


def should_show_attendance_clock() -> bool:
    return get_normalized_role() in [ROLE_EMPLOYEE, ROLE_CLEANER]


def set_main_view(view_name: str) -> None:
    st.session_state[SESSION_MAIN_VIEW] = view_name


def get_main_view() -> str:
    return st.session_state.get(SESSION_MAIN_VIEW, NAV_DASHBOARD)


def normalize_financial_records(records: list) -> list:
    normalized = []

    for record in records or []:
        normalized.append(
            {
                "date": record.get("date", "-"),
                "amount": float(record.get("amount", record.get("val", 0)) or 0),
                "note": record.get("note", "-"),
            }
        )

    return normalized


def calculate_salary_breakdown(user_info: dict) -> dict:
    salary_basic = float(user_info.get("salary_basic", 0) or 0)
    transport_allowance = float(user_info.get("transport_allowance", 0) or 0)
    communication_allowance = float(user_info.get("communication_allowance", 0) or 0)
    other_allowance = float(user_info.get("other_allowance", 0) or 0)

    total_fixed = (
        salary_basic
        + transport_allowance
        + communication_allowance
        + other_allowance
    )

    total_bonus = sum(float(item.get("amount", 0) or 0) for item in user_info.get("bonus", []))
    total_overtime = sum(float(item.get("amount", 0) or 0) for item in user_info.get("overtime", []))
    total_deductions = sum(float(item.get("amount", 0) or 0) for item in user_info.get("deductions", []))
    total_advances = sum(float(item.get("amount", 0) or 0) for item in user_info.get("advances", []))
    total_late_penalties = sum(float(item.get("amount", 0) or 0) for item in user_info.get("late_penalties", []))
    total_absence_penalties = sum(float(item.get("amount", 0) or 0) for item in user_info.get("absence_penalties", []))

    gross_salary = total_fixed + total_bonus + total_overtime
    total_withheld = total_deductions + total_advances + total_late_penalties + total_absence_penalties
    net_salary = gross_salary - total_withheld

    return {
        "salary_basic": salary_basic,
        "transport_allowance": transport_allowance,
        "communication_allowance": communication_allowance,
        "other_allowance": other_allowance,
        "total_fixed": total_fixed,
        "total_bonus": total_bonus,
        "total_overtime": total_overtime,
        "total_deductions": total_deductions,
        "total_advances": total_advances,
        "total_late_penalties": total_late_penalties,
        "total_absence_penalties": total_absence_penalties,
        "gross_salary": gross_salary,
        "total_withheld": total_withheld,
        "net_salary": net_salary,
    }


def get_training_status(username: str) -> dict:
    return db.get("training_records", {}).get(username, {})


# =========================
# Draft helpers
# =========================
def get_draft_prefixes() -> tuple[str, ...]:
    return (
        "s_",
        "o_",
        "e_",
        "c_",
        "m_",
        "i_",
        "ks",
        "xs",
        "op",
        "u10",
        "v22",
        "ex",
        "kj",
        "xj",
        "dn",
        "k1",
        "k2",
        "x1",
        "x2",
        "open_",
        "close_",
        "debt_",
        "crm_",
        "attendance_",
        "direct_login_",
        "ops_",
    )


def collect_current_draft_data() -> dict:
    prefixes = get_draft_prefixes()

    draft_data = {}
    for key, value in st.session_state.items():
        if key.startswith(prefixes):
            draft_data[key] = value

    return draft_data


def hydrate_user_drafts_once() -> None:
    if not is_logged_in():
        return

    if st.session_state.get(SESSION_DRAFTS_LOADED, False):
        return

    username = get_current_username()
    if not username:
        return

    try:
        draft_data = load_user_draft(username)
        if isinstance(draft_data, dict) and draft_data:
            for key, value in draft_data.items():
                if key not in st.session_state:
                    st.session_state[key] = value
    except Exception:
        pass

    st.session_state[SESSION_DRAFTS_LOADED] = True


def autosave_current_user_draft(force: bool = False) -> None:
    if not is_logged_in():
        return

    username = get_current_username()
    if not username:
        return

    now_ts = time.time()
    last_ts = float(st.session_state.get(SESSION_LAST_DRAFT_SAVE_TS, 0.0) or 0.0)

    if not force and (now_ts - last_ts) < AUTOSAVE_INTERVAL_SECONDS:
        return

    draft_data = collect_current_draft_data()
    if not draft_data:
        st.session_state[SESSION_LAST_DRAFT_SAVE_TS] = now_ts
        return

    try:
        save_user_draft(username, draft_data)
    except Exception:
        pass

    st.session_state[SESSION_LAST_DRAFT_SAVE_TS] = now_ts


# =========================
# Supabase import manager
# =========================
def render_supabase_import_manager() -> None:
    if not can_open_backup_manager():
        return

    st.markdown("### ☁️ Import Backup To Supabase")
    st.info("ارفع ملف النسخة الاحتياطية JSON ثم اضغط استيراد إلى Supabase.")

    uploaded_backup = st.file_uploader(
        "Upload Backup JSON File",
        type=["json"],
        key="supabase_backup_upload",
    )

    if uploaded_backup is not None:
        st.success(f"Selected file: {uploaded_backup.name}")

        if st.button("🚀 Import Backup To Supabase", use_container_width=True):
            try:
                backup_folder = "backups"
                os.makedirs(backup_folder, exist_ok=True)

                temp_backup_path = os.path.join(backup_folder, uploaded_backup.name)

                with open(temp_backup_path, "wb") as f:
                    f.write(uploaded_backup.getbuffer())

                migrate(temp_backup_path)
                cached_load_db.clear()
                st.success("✅ Backup imported to Supabase successfully.")
                st.rerun()

            except Exception as e:
                st.error(f"Import failed: {e}")


# =========================
# Employee profile (main area)
# =========================
def render_profile_identity_tab(user_info: dict) -> None:
    col1, col2 = st.columns([1, 3])

    with col1:
        safe_user_image(user_info, width=150)

    with col2:
        st.subheader(user_info.get("full_name", get_current_username() or "User"))
        st.write(f"**Role:** {get_role_label(user_info.get('role', 'employee'))}")
        st.write(f"**Job Title:** {user_info.get('job_title', '-')}")
        st.write(f"**Employee Code:** {user_info.get('employee_code', '-') or '-'}")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Birth Date:** {user_info.get('birth_date', '-')}")
        st.write(f"**Hiring Date:** {user_info.get('hiring_date', '-')}")
        st.write(f"**Phone:** {user_info.get('phone', '-') or '-'}")
        st.write(f"**Email:** {user_info.get('email', '-') or '-'}")

    with c2:
        st.write(f"**National ID:** {user_info.get('national_id', '-') or '-'}")
        st.write(f"**Bank Name:** {user_info.get('bank_name', '-') or '-'}")
        st.write(f"**Bank Account / IBAN:** {user_info.get('bank_account_number', '-') or '-'}")
        st.write(f"**Wallet Number:** {user_info.get('wallet_number', '-') or '-'}")


def render_profile_salary_tab(user_info: dict) -> None:
    st.subheader("💳 Salary & Payout Details")

    salary_summary = calculate_salary_breakdown(user_info)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Fixed Salary", f"{salary_summary['total_fixed']:,.2f} LE")
    with c2:
        st.metric("Gross Salary", f"{salary_summary['gross_salary']:,.2f} LE")
    with c3:
        st.metric("Net Salary", f"{salary_summary['net_salary']:,.2f} LE")

    salary_df = pd.DataFrame(
        [
            {"Item": "Basic Salary", "Value": salary_summary["salary_basic"]},
            {"Item": "Transport Allowance", "Value": salary_summary["transport_allowance"]},
            {"Item": "Communication Allowance", "Value": salary_summary["communication_allowance"]},
            {"Item": "Other Allowance", "Value": salary_summary["other_allowance"]},
            {"Item": "Total Bonus", "Value": salary_summary["total_bonus"]},
            {"Item": "Total Overtime", "Value": salary_summary["total_overtime"]},
            {"Item": "Total Deductions", "Value": salary_summary["total_deductions"]},
            {"Item": "Total Advances", "Value": salary_summary["total_advances"]},
            {"Item": "Late Penalties", "Value": salary_summary["total_late_penalties"]},
            {"Item": "Absence Penalties", "Value": salary_summary["total_absence_penalties"]},
            {"Item": "Net Salary", "Value": salary_summary["net_salary"]},
        ]
    )

    st.dataframe(
        salary_df,
        use_container_width=True,
        column_config={
            "Value": st.column_config.NumberColumn("Value", format="%.2f LE"),
        },
    )

    st.write(f"**Payout Method:** {get_payout_method_label(user_info.get('payout_method', 'bank'))}")


def render_profile_warnings_tab(user_info: dict) -> None:
    st.subheader("🚨 Warnings")

    warnings = user_info.get("warnings", [])
    if warnings:
        warnings_df = pd.DataFrame(
            [
                {
                    "Date": item.get("date", "-"),
                    "Note": item.get("note", "-"),
                }
                for item in warnings
            ]
        )
        st.dataframe(warnings_df, use_container_width=True)
    else:
        st.success("No warnings recorded.")


def render_profile_records_tab(user_info: dict) -> None:
    st.subheader("📌 HR Records")

    for category in HR_RECORD_KEYS:
        label = HR_RECORD_LABELS.get(category, category.title())

        with st.expander(label, expanded=False):
            records = normalize_financial_records(user_info.get(category, []))
            if records:
                st.dataframe(
                    pd.DataFrame(records),
                    use_container_width=True,
                    column_config={
                        "amount": st.column_config.NumberColumn("Amount", format="%.2f LE"),
                        "date": "Date",
                        "note": "Note",
                    },
                )
            else:
                st.info(f"No {label.lower()} records yet.")


def render_profile_training_tab() -> None:
    render_training_service_module(db, admin_mode=False)


def render_profile_page() -> None:
    user_info = get_current_user()

    st.title("👤 My Profile")
    st.caption("كل بياناتك الشخصية والوظيفية في مكان واحد.")

    tabs = st.tabs(
        [
            "Personal Info",
            "Salary",
            "Warnings",
            "HR Records",
            "Training",
        ]
    )

    with tabs[0]:
        render_profile_identity_tab(user_info)

    with tabs[1]:
        render_profile_salary_tab(user_info)

    with tabs[2]:
        render_profile_warnings_tab(user_info)

    with tabs[3]:
        render_profile_records_tab(user_info)

    with tabs[4]:
        render_profile_training_tab()


# =========================
# Birthday page
# =========================
def render_birthday_page() -> None:
    birthday_ui()


# =========================
# CRM placeholder / entry point
# =========================
def render_crm_module() -> None:
    try:
        from crm_ui import crm_ui
        crm_ui()
        return
    except Exception:
        pass

    try:
        from crm_service import get_crm_dashboard_stats

        st.subheader("📇 CRM & Internal Communication")
        st.info("الخدمات الأساسية للـ CRM موجودة، وواجهة الـ UI الكاملة هنكملها بعد هذه المرحلة.")

        stats = get_crm_dashboard_stats(db, get_current_username())
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("My Tasks", stats.get("my_tasks_total", 0))
        with c2:
            st.metric("Unread Messages", stats.get("my_unread_messages", 0))
        with c3:
            st.metric("Unread Notifications", stats.get("my_unread_notifications", 0))

        st.caption("لو عندك ملف crm_ui.py بعد كده، main.py جاهز يقرأه مباشرة.")
    except Exception as e:
        st.error(f"CRM module failed to load: {e}")


# =========================
# Admin modules
# =========================
def render_hr_module() -> None:
    from hr_service import hr_management_ui
    hr_management_ui(db)


def render_payroll_module() -> None:
    st.subheader("💰 Payroll & Money")
    st.info("Manage Salaries, Bonuses & Deductions")

    users = list(db.get("users", {}).keys())
    if not users:
        st.warning("No employees found.")
        return

    target = st.selectbox("Select Employee", users)
    user_fin = db["users"].get(target, {})

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        salary = st.number_input(
            "Base Salary",
            min_value=0.0,
            value=float(user_fin.get("salary", 0) or 0),
            step=100.0,
        )
    with col_s2:
        hiring_date = st.date_input(
            "Hiring Date",
            value=parse_hiring_date(user_fin.get("hiring_date", "2024-01-01")),
        )

    if st.button("💾 Update Contract"):
        db["users"][target]["salary"] = salary
        db["users"][target]["hiring_date"] = str(hiring_date)
        persist_db_and_rerun("Contract Updated")

    st.divider()
    st.write("**Add Financial Entry:**")

    entry_type = st.radio(
        "Type",
        list(PAYROLL_ENTRY_KEY_MAP.keys()),
        horizontal=True,
    )
    amount = st.number_input("Value (LE)", min_value=0.0, step=10.0)
    note = st.text_input("Reason / Note")

    if st.button("✅ Submit Entry"):
        target_key = PAYROLL_ENTRY_KEY_MAP[entry_type]
        db["users"][target].setdefault(target_key, [])
        db["users"][target][target_key].append(
            {
                "date": str(date.today()),
                "amount": amount,
                "note": note.strip(),
            }
        )
        persist_db_and_rerun("Added to HR Record")


def render_tasks_module() -> None:
    from task_service import add_task, delete_task, get_tasks_by_category

    st.subheader("📝 Tasks & Checklists")
    st.info("Manage operational tasks and checklists")

    category = st.selectbox("Category", TASK_CATEGORIES, key="tasks_category_select")
    task_rows = get_tasks_by_category(category)

    if task_rows:
        for row in task_rows:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.text(f"📌 {row.get('task_text', '')}")
            with c2:
                if st.button("🗑️", key=f"del_task_{row['id']}"):
                    success, message = delete_task(row["id"])
                    if success:
                        cached_load_db.clear()
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("No tasks found in this category.")

    new_task = st.text_input("New Task", key="new_task_text")
    if st.button("➕ Add Task"):
        success, message = add_task(category, new_task)
        if success:
            cached_load_db.clear()
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def render_branches_expenses_module() -> None:
    st.subheader("🏢 Branches & Expenses")
    st.info("Manage Locations & Expenses")

    st.write("**🏢 Branches (الفروع)**")
    branches = db.setdefault("branches", [])

    if branches:
        branch_selected = st.selectbox("Select Branch", branches)
        c_br1, c_br2 = st.columns(2)

        with c_br1:
            new_branch_name = st.text_input("Rename Branch", value=branch_selected)
            if st.button("✏️ Rename"):
                if new_branch_name.strip():
                    idx = branches.index(branch_selected)
                    branches[idx] = new_branch_name.strip()
                    persist_db_and_rerun("Renamed!")

        with c_br2:
            if st.button("🗑️ Delete Branch", type="primary"):
                branches.remove(branch_selected)
                persist_db_and_rerun("Deleted!")
    else:
        st.info("No branches yet.")

    new_branch = st.text_input("New Branch Name")
    if st.button("➕ Create Branch"):
        if new_branch.strip():
            branches.append(new_branch.strip())
            persist_db_and_rerun()

    st.divider()
    st.write("**💸 Expense Categories (بنود المصاريف)**")

    db.setdefault("expense_categories", [])
    for index, expense in enumerate(db["expense_categories"]):
        ce1, ce2 = st.columns([5, 1])
        with ce1:
            st.text(f"🔹 {expense}")
        with ce2:
            if st.button("✖️", key=f"del_ex_{index}"):
                db["expense_categories"].pop(index)
                persist_db_and_rerun()

    new_expense = st.text_input("New Expense Category")
    if st.button("➕ Add Expense Category"):
        if new_expense.strip():
            db["expense_categories"].append(new_expense.strip())
            persist_db_and_rerun()


def render_archive_history_module() -> None:
    st.subheader("📂 Archive & History")

    if not can_open_admin_panel():
        st.error("Access Denied.")
        return

    history = db.get("history", [])
    if not history:
        st.info("No archived shifts found yet.")
        return

    try:
        total_sales = sum(float(item.get("sales", 0) or 0) for item in history)
        total_expenses = sum(float(item.get("expenses", 0) or 0) for item in history)
        total_diff = sum(float(item.get("diff", 0) or 0) for item in history)
    except ValueError:
        st.error("Error in data types within History. Please check database.")
        total_sales = total_expenses = total_diff = 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Sales", f"{total_sales:,.2f} LE")
    m2.metric("Total Expenses", f"{total_expenses:,.2f} LE")
    m3.metric("Net Cash Diff", f"{total_diff:,.2f} LE", delta=total_diff, delta_color="normal")

    st.divider()
    st.write("### 📜 Detailed Shift History")

    df_history = pd.DataFrame(reversed(history))

    column_mapping = {
        "date": "Date",
        "staff": "Employee",
        "staff_username": "Username",
        "role": "Role",
        "branch": "Branch",
        "shift": "Shift",
        "sales": "Sales",
        "expenses": "Expenses",
        "exp_note": "Exp. Details",
        "diff": "Cash Diff",
        "t_open": "Opening Cash",
        "t_close": "Closing Cash",
        "social_notes": "Social Notes",
        "interaction_notes": "Interaction Notes",
        "special_notes": "Special Notes",
    }

    existing_columns = {
        old_name: new_name
        for old_name, new_name in column_mapping.items()
        if old_name in df_history.columns
    }

    if "role" in df_history.columns:
        df_history["role"] = df_history["role"].apply(get_role_label)

    st.dataframe(
        df_history.rename(columns=existing_columns),
        use_container_width=True,
        column_config={
            "Sales": st.column_config.NumberColumn(format="%.2f LE"),
            "Expenses": st.column_config.NumberColumn(format="%.2f LE"),
            "Cash Diff": st.column_config.NumberColumn(format="%.2f LE"),
            "Opening Cash": st.column_config.NumberColumn(format="%.2f LE"),
            "Closing Cash": st.column_config.NumberColumn(format="%.2f LE"),
        },
    )

    st.divider()
    with st.expander("🗑️ Advanced Settings (Danger Zone)"):
        st.warning("Action below is irreversible!")
        confirm_check = st.checkbox("I understand that 'Clear History' will delete everything.")
        if confirm_check and st.button("🚨 Permanently Clear All History"):
            db["history"] = []
            persist_db_and_rerun("History Cleared!")


def render_training_module() -> None:
    render_training_service_module(db, admin_mode=True)


def render_printer_management_module() -> None:
    st.subheader("🖨 Printer Management")
    printer_management_ui(db)


def render_role_management_module() -> None:
    try:
        from role_management_service import role_management_ui
        role_management_ui()
    except Exception as e:
        st.error(f"Role management failed to load: {e}")


def render_admin_panel_main() -> None:
    if not can_open_admin_panel():
        st.error("Access denied.")
        return

    st.title("⚙️ Admin Panel")
    st.caption("اختر القسم من القائمة التالية، وسيظهر المحتوى هنا في منتصف الشاشة.")

    admin_choice = st.selectbox(
        "Select Management Module",
        ADMIN_MODULE_OPTIONS,
        key="admin_main_selectbox",
    )

    st.divider()

    if admin_choice == ADMIN_MODULE_HR:
        render_hr_module()
    elif admin_choice == ADMIN_MODULE_PAYROLL:
        render_payroll_module()
    elif admin_choice == ADMIN_MODULE_TASKS:
        render_tasks_module()
    elif admin_choice == ADMIN_MODULE_BRANCHES:
        render_branches_expenses_module()
    elif admin_choice == ADMIN_MODULE_PRINTERS:
        render_printer_management_module()
    elif admin_choice == ADMIN_MODULE_ARCHIVE:
        render_archive_history_module()
    elif admin_choice == ADMIN_MODULE_TRAINING:
        render_training_module()
    elif admin_choice == ADMIN_MODULE_ROLE_MANAGEMENT:
        render_role_management_module()
    elif admin_choice == ADMIN_MODULE_CRM:
        render_crm_module()
    else:
        st.info("This module is not configured yet.")


# =========================
# Sidebar
# =========================
def render_sidebar() -> None:
    with st.sidebar:
        user_info = get_current_user()
        current_role = get_current_role()
        current_view = get_main_view()

        safe_user_image(user_info, width=100)
        st.header(user_info.get("full_name", get_current_username() or "User"))
        st.caption(f"Role: {get_role_label(current_role)}")
        st.caption(f"Job Title: {user_info.get('job_title', '-')}")

        st.divider()
        st.write("### Navigation")

        if st.button(
            "🏠 Dashboard",
            use_container_width=True,
            type="primary" if current_view == NAV_DASHBOARD else "secondary",
        ):
            set_main_view(NAV_DASHBOARD)
            st.rerun()

        if st.button(
            "👤 My Profile",
            use_container_width=True,
            type="primary" if current_view == NAV_PROFILE else "secondary",
        ):
            set_main_view(NAV_PROFILE)
            st.rerun()

        if st.button(
            "📊 Daily Operations",
            use_container_width=True,
            type="primary" if current_view == NAV_OPERATIONS else "secondary",
        ):
            set_main_view(NAV_OPERATIONS)
            st.rerun()

        if st.button(
            "🎂 Birthdays",
            use_container_width=True,
            type="primary" if current_view == NAV_BIRTHDAY else "secondary",
        ):
            set_main_view(NAV_BIRTHDAY)
            st.rerun()

        if can_open_admin_panel():
            if st.button(
                "⚙️ Admin Panel",
                use_container_width=True,
                type="primary" if current_view == NAV_ADMIN else "secondary",
            ):
                set_main_view(NAV_ADMIN)
                st.rerun()

        if can_open_backup_manager():
            if st.button(
                "🧰 Backup Manager",
                use_container_width=True,
                type="primary" if current_view == NAV_BACKUP else "secondary",
            ):
                set_main_view(NAV_BACKUP)
                st.rerun()

        st.divider()

        if st.button("💾 Save Draft Now", use_container_width=True):
            autosave_current_user_draft(force=True)
            st.success("Draft saved.")

        if st.button("🚪 Logout", use_container_width=True):
            autosave_current_user_draft(force=True)
            logout_user(db)
            st.rerun()


# =========================
# Dashboard / Backup / Main views
# =========================
def render_dashboard_page() -> None:
    user_info = get_current_user()
    username = get_current_username() or "-"
    current_role = get_current_role()
    normalized_role = get_normalized_role()
    training_info = get_training_status(username)

    st.title("🏠 Dashboard")
    st.caption("واجهة رئيسية أوضح وأذكى حسب دور المستخدم.")

    render_attendance_clock_widget()

    top1, top2, top3 = st.columns(3)
    with top1:
        st.metric("User", username)
    with top2:
        st.metric("Role", get_role_label(current_role))
    with top3:
        st.metric("Training", training_info.get("status", "pending") if training_info else "pending")

    st.divider()

    render_role_dashboard_cards(
        normalized_role=normalized_role,
        user_info=user_info,
        db=db,
        training_info=training_info,
    )

    st.divider()

    st.subheader("Quick Access")

    quick_buttons = [
        ("👤 Open My Profile", NAV_PROFILE),
        ("📊 Open Daily Operations", NAV_OPERATIONS),
        ("🎂 Open Birthdays", NAV_BIRTHDAY),
    ]

    if can_open_admin_panel():
        quick_buttons.append(("⚙️ Open Admin Panel", NAV_ADMIN))

    if can_open_backup_manager():
        quick_buttons.append(("🧰 Open Backup Manager", NAV_BACKUP))

    cols = st.columns(len(quick_buttons))
    for idx, (label, target_view) in enumerate(quick_buttons):
        with cols[idx]:
            if st.button(label, use_container_width=True, key=f"quick_btn_{idx}"):
                set_main_view(target_view)
                st.rerun()

    st.divider()

    st.subheader("Summary")
    st.write(f"**Full Name:** {user_info.get('full_name', '-')}")
    st.write(f"**Job Title:** {user_info.get('job_title', '-')}")
    st.write(f"**Employee Code:** {user_info.get('employee_code', '-') or '-'}")

    if normalized_role == ROLE_EMPLOYEE:
        st.info("يمكنك استخدام الأقسام المخصصة لك فقط حسب صلاحياتك.")
    elif normalized_role == ROLE_CLEANER:
        st.info("يمكنك استخدام أقسام النظافة والتقرير حسب صلاحياتك.")
    elif not can_access_daily_operations():
        st.warning(get_daily_operations_block_message())


def render_backup_manager_page() -> None:
    if not can_open_backup_manager():
        st.error("Access denied.")
        return

    st.title("🧰 Backup Manager")

    backup_folder = "backups"
    os.makedirs(backup_folder, exist_ok=True)

    with st.expander("☁️ Import Backup To Supabase", expanded=True):
        render_supabase_import_manager()

    st.divider()

    st.subheader("📥 Latest Backup Download")

    backup_files = sorted(os.listdir(backup_folder), reverse=True)

    if not backup_files:
        st.warning("لا توجد نسخ احتياطية حتى الآن.")
    else:
        latest_file = backup_files[0]
        latest_path = os.path.join(backup_folder, latest_file)

        st.info(f"🕒 أحدث نسخة: {latest_file}")

        with open(latest_path, "rb") as f:
            st.download_button(
                "📥 تحميل النسخة الاحتياطية",
                f,
                file_name=latest_file,
            )

    st.divider()
    st.subheader("♻️ Restore Old Backup")

    backup_files = sorted(os.listdir(backup_folder), reverse=True)
    if not backup_files:
        st.info("لا توجد ملفات نسخ احتياطية للاسترجاع.")
        return

    restore_file = st.selectbox("اختر نسخة احتياطية", backup_files)

    if st.button("♻️ استرجاع النسخة المحددة"):
        selected_path = os.path.join(backup_folder, restore_file)
        with open(selected_path, "r", encoding="utf-8") as f:
            restored_data = json.load(f)

        db.clear()
        db.update(restored_data)
        save_db(db)
        cached_load_db.clear()
        st.success("✅ تم استرجاع النسخة بنجاح")
        st.rerun()


def render_blocked_daily_operations_view() -> None:
    st.title("📊 Daily Operations")
    st.warning(get_daily_operations_block_message())


def render_main_content() -> None:
    current_view = get_main_view()

    if current_view == NAV_PROFILE:
        render_profile_page()
        return

    if current_view == NAV_OPERATIONS:
        if can_access_daily_operations():
            daily_operations_ui(db)
        else:
            render_blocked_daily_operations_view()
        return

    if current_view == NAV_BIRTHDAY:
        render_birthday_page()
        return

    if current_view == NAV_ADMIN:
        if can_open_admin_panel():
            render_admin_panel_main()
        else:
            st.error("Access denied.")
        return

    if current_view == NAV_BACKUP:
        render_backup_manager_page()
        return

    render_dashboard_page()


# =========================
# Main app
# =========================
def main() -> None:
    ensure_db_defaults()
    ensure_ui_defaults()

    if not is_logged_in():
        render_login_screen(db)

    hydrate_user_drafts_once()
    autosave_current_user_draft(force=False)

    render_sidebar()

    if is_logged_in() and st.session_state.get(SESSION_USER):
        render_main_content()


if __name__ == "__main__":
    main()
