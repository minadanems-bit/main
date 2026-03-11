# =====================================================
# DATABASE LAYER (SUPABASE VERSION - CLEAN REFACTOR)
# =====================================================

from __future__ import annotations

from typing import Any

import streamlit as st
from supabase import Client, create_client

from constants import (
    DEFAULT_APP_DATA,
    DEFAULT_BIRTH_DATE,
    DEFAULT_HIRING_DATE,
    DEFAULT_MANAGER_PHONE,
    DEFAULT_USER_SCHEMA,
    HR_RECORD_KEYS,
    TASK_CATEGORIES,
)


# =====================================================
# Extra financial record keys
# =====================================================
EXTRA_FINANCIAL_RECORD_KEYS = [
    "advances",
    "late_penalties",
    "absence_penalties",
]

ALL_FINANCIAL_RECORD_KEYS = list(HR_RECORD_KEYS) + EXTRA_FINANCIAL_RECORD_KEYS


# =====================================================
# Connection
# =====================================================
@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


# =====================================================
# Generic helpers
# =====================================================
def safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _empty_logo_to_none(value: Any) -> Any:
    if value == "":
        return None
    return value


# =====================================================
# User normalization
# =====================================================
def normalize_user_row(row: dict) -> dict:
    user = dict(DEFAULT_USER_SCHEMA)

    user.update(
        {
            "pass": row.get("password", ""),
            "role": row.get("role", "employee"),
            "full_name": row.get("full_name", row.get("username", "")),
            "job_title": row.get("job_title", ""),
            "photo": row.get("photo"),
            "id_card": row.get("id_card"),
            "employee_code": row.get("employee_code", ""),
            "birth_date": safe_str(row.get("birth_date", DEFAULT_BIRTH_DATE), DEFAULT_BIRTH_DATE),
            "phone": row.get("phone", ""),
            "email": row.get("email", ""),
            "national_id": row.get("national_id", ""),
            "address": row.get("address", ""),
            "qualification": row.get("qualification", ""),
            "hiring_date": safe_str(row.get("hiring_date", DEFAULT_HIRING_DATE), DEFAULT_HIRING_DATE),
            "salary": safe_float(row.get("salary", 0)),
            "salary_basic": safe_float(row.get("salary_basic", 0)),
            "transport_allowance": safe_float(row.get("transport_allowance", 0)),
            "communication_allowance": safe_float(row.get("communication_allowance", 0)),
            "other_allowance": safe_float(row.get("other_allowance", 0)),
            "bank_name": row.get("bank_name", ""),
            "bank_account_number": row.get("bank_account_number", ""),
            "wallet_number": row.get("wallet_number", ""),
            "payout_method": row.get("payout_method", "bank"),
            "warnings": safe_list(row.get("warnings")),
            "bonus": [],
            "deductions": [],
            "overtime": [],
            "extra_leaves": [],
            "advances": [],
            "late_penalties": [],
            "absence_penalties": [],
        }
    )

    return user


def attach_financial_records(users: dict, financial_rows: list) -> dict:
    valid_record_types = set(ALL_FINANCIAL_RECORD_KEYS)

    for item in financial_rows:
        username = item.get("username")
        if username not in users:
            continue

        record_type = item.get("record_type", "")
        if record_type not in valid_record_types:
            continue

        users[username].setdefault(record_type, [])
        users[username][record_type].append(
            {
                "date": safe_str(item.get("record_date", "")),
                "amount": safe_float(item.get("amount", 0)),
                "note": item.get("note", ""),
            }
        )

    return users


# =====================================================
# Read helpers
# =====================================================
def _load_users(supabase: Client) -> dict:
    result = supabase.table("users").select("*").execute()
    rows = result.data or []

    users = {}
    for row in rows:
        username = row.get("username")
        if username:
            users[username] = normalize_user_row(row)

    fin_result = supabase.table("employee_financial_records").select("*").execute()
    fin_rows = fin_result.data or []
    return attach_financial_records(users, fin_rows)


def _load_tasks(supabase: Client) -> dict:
    result = supabase.table("tasks").select("*").execute()
    rows = result.data or []

    tasks = {category: [] for category in TASK_CATEGORIES}
    for row in rows:
        category = row.get("category", "")
        task_text = row.get("task_text", "")
        if category in tasks and task_text:
            tasks[category].append(task_text)

    return tasks


def _load_branches(supabase: Client) -> list:
    result = supabase.table("branches").select("*").execute()
    rows = result.data or []
    return [row.get("branch_name", "") for row in rows if row.get("branch_name")]


def _load_expense_categories(supabase: Client) -> list:
    result = supabase.table("expense_categories").select("*").execute()
    rows = result.data or []
    return [row.get("category_name", "") for row in rows if row.get("category_name")]


def _load_printers(supabase: Client) -> dict:
    result = supabase.table("printers").select("*").execute()
    rows = result.data or []

    return {
        row.get("printer_name", ""): row.get("printer_ip", "")
        for row in rows
        if row.get("printer_name")
    }


def _load_history(supabase: Client) -> list:
    result = supabase.table("shift_history").select("*").order("created_at").execute()
    rows = result.data or []

    history = []
    for row in rows:
        history.append(
            {
                "date": safe_str(row.get("report_date", "")),
                "branch": row.get("branch", ""),
                "shift": row.get("shift", ""),
                "staff": row.get("staff", ""),
                "staff_username": row.get("staff_username", ""),
                "role": row.get("role", ""),
                "job_title": row.get("job_title", ""),
                "report_type": row.get("report_type", ""),
                "sales": safe_float(row.get("sales", 0)),
                "expenses": safe_float(row.get("expenses", 0)),
                "expenses_list": safe_list(row.get("expenses_list")),
                "exp_note": row.get("exp_note", ""),
                "diff": safe_float(row.get("diff", 0)),
                "t_open": safe_float(row.get("t_open", 0)),
                "t_close": safe_float(row.get("t_close", 0)),
                "cash_breakdown": safe_dict(row.get("cash_breakdown")),
                "closing_cash_breakdown": safe_dict(row.get("closing_cash_breakdown")),
                "opay_open": safe_float(row.get("opay_open", 0)),
                "opay_close": safe_float(row.get("opay_close", 0)),
                "opay_diff": safe_float(row.get("opay_diff", 0)),
                "debit_open": safe_float(row.get("debit_open", 0)),
                "debit_close": safe_float(row.get("debit_close", 0)),
                "debit_diff": safe_float(row.get("debit_diff", 0)),
                "nbe_open": safe_float(row.get("nbe_open", 0)),
                "nbe_close": safe_float(row.get("nbe_close", 0)),
                "nbe_diff": safe_float(row.get("nbe_diff", 0)),
                "qnb_open": safe_float(row.get("qnb_open", 0)),
                "qnb_close": safe_float(row.get("qnb_close", 0)),
                "qnb_diff": safe_float(row.get("qnb_diff", 0)),
                "fawry_open": safe_float(row.get("fawry_open", 0)),
                "fawry_close": safe_float(row.get("fawry_close", 0)),
                "fawry_diff": safe_float(row.get("fawry_diff", 0)),
                "customer_debts": safe_list(row.get("customer_debts")),
                "printer_diff": safe_dict(row.get("printer_diff")),
                "social_notes": row.get("social_notes", ""),
                "interaction_notes": row.get("interaction_notes", ""),
                "special_notes": row.get("special_notes", ""),
                "visible_sections": safe_list(row.get("visible_sections")),
            }
        )

    return history


def _load_training_records(supabase: Client) -> dict:
    result = supabase.table("training_records").select("*").execute()
    rows = result.data or []

    records = {}
    for row in rows:
        username = row.get("username")
        if username:
            records[username] = {
                "date": safe_str(row.get("record_date", "")),
                "status": row.get("status", "completed"),
            }

    return records


def _load_attendance_records(supabase: Client) -> dict:
    try:
        result = supabase.table("attendance_records").select("*").order("created_at").execute()
        rows = result.data or []
    except Exception:
        return {}

    attendance_records = {}

    for row in rows:
        month_key = safe_str(row.get("month_key", ""))
        username = safe_str(row.get("username", ""))

        if not month_key or not username:
            continue

        attendance_records.setdefault(month_key, {})
        attendance_records[month_key].setdefault(username, [])
        attendance_records[month_key][username].append(
            {
                "date": safe_str(row.get("attendance_date", "")),
                "time": safe_str(row.get("attendance_time", "")),
                "shift": safe_str(row.get("shift", "")),
                "late_minutes": int(safe_float(row.get("late_minutes", 0))),
                "status": safe_str(row.get("status", "")),
                "created_at": safe_str(row.get("created_at", "")),
            }
        )

    return attendance_records


def _load_late_tracking(supabase: Client) -> dict:
    try:
        result = supabase.table("late_tracking").select("*").execute()
        rows = result.data or []
    except Exception:
        return {}

    data = {}
    for row in rows:
        month_key = safe_str(row.get("month_key", ""))
        username = safe_str(row.get("username", ""))
        late_count = int(safe_float(row.get("late_count", 0)))

        if not month_key or not username:
            continue

        data.setdefault(month_key, {})
        data[month_key][username] = late_count

    return data


def _load_blocked_users(supabase: Client) -> dict:
    try:
        result = supabase.table("blocked_users").select("*").execute()
        rows = result.data or []
    except Exception:
        return {}

    data = {}
    for row in rows:
        month_key = safe_str(row.get("month_key", ""))
        username = safe_str(row.get("username", ""))
        is_blocked = bool(row.get("is_blocked", False))

        if not month_key or not username:
            continue

        data.setdefault(month_key, {})
        data[month_key][username] = is_blocked

    return data


def _load_settings(supabase: Client) -> tuple[str, Any]:
    result = supabase.table("app_settings").select("*").execute()
    rows = result.data or []

    settings_map = {}
    for row in rows:
        settings_map[row.get("setting_key")] = row.get("setting_value")

    manager_phone = safe_str(settings_map.get("manager_phone", DEFAULT_MANAGER_PHONE), DEFAULT_MANAGER_PHONE)
    logo = _empty_logo_to_none(settings_map.get("logo", None))
    return manager_phone, logo


# =====================================================
# Main load
# =====================================================
def load_db() -> dict:
    supabase = get_supabase()

    users = _load_users(supabase)
    tasks = _load_tasks(supabase)
    branches = _load_branches(supabase)
    expense_categories = _load_expense_categories(supabase)
    printers = _load_printers(supabase)
    history = _load_history(supabase)
    training_records = _load_training_records(supabase)
    attendance_records = _load_attendance_records(supabase)
    late_tracking = _load_late_tracking(supabase)
    blocked_users = _load_blocked_users(supabase)
    manager_phone, logo = _load_settings(supabase)

    data = dict(DEFAULT_APP_DATA)
    data.update(
        {
            "logo": logo,
            "manager_phone": manager_phone,
            "branches": branches,
            "expense_categories": expense_categories,
            "users": users,
            "tasks": tasks,
            "history": history,
            "drafts": {},
            "logs": [],
            "training_records": training_records,
            "printers": printers,
            "attendance_records": attendance_records,
            "late_tracking": late_tracking,
            "blocked_users": blocked_users,
        }
    )
    return data


# =====================================================
# Write helpers
# =====================================================
def _delete_all(supabase: Client, table_name: str, guard_column: str) -> None:
    supabase.table(table_name).delete().neq(guard_column, "__never__").execute()


def _upsert_settings(supabase: Client, data: dict) -> None:
    logo_value = data.get("logo", "")
    if logo_value is None:
        logo_value = ""

    supabase.table("app_settings").upsert(
        [
            {
                "setting_key": "manager_phone",
                "setting_value": safe_str(data.get("manager_phone", DEFAULT_MANAGER_PHONE), DEFAULT_MANAGER_PHONE),
            },
            {
                "setting_key": "logo",
                "setting_value": logo_value,
            },
        ],
        on_conflict="setting_key",
    ).execute()


def _write_users(supabase: Client, users: dict) -> None:
    user_rows = []
    financial_rows = []

    for username, user in safe_dict(users).items():
        user_rows.append(
            {
                "username": username,
                "password": user.get("pass", ""),
                "role": user.get("role", "employee"),
                "full_name": user.get("full_name", username),
                "job_title": user.get("job_title", ""),
                "photo": user.get("photo"),
                "id_card": user.get("id_card"),
                "employee_code": user.get("employee_code", ""),
                "birth_date": user.get("birth_date", DEFAULT_BIRTH_DATE),
                "phone": user.get("phone", ""),
                "email": user.get("email", ""),
                "national_id": user.get("national_id", ""),
                "address": user.get("address", ""),
                "qualification": user.get("qualification", ""),
                "hiring_date": user.get("hiring_date", DEFAULT_HIRING_DATE),
                "salary": safe_float(user.get("salary", 0)),
                "salary_basic": safe_float(user.get("salary_basic", 0)),
                "transport_allowance": safe_float(user.get("transport_allowance", 0)),
                "communication_allowance": safe_float(user.get("communication_allowance", 0)),
                "other_allowance": safe_float(user.get("other_allowance", 0)),
                "bank_name": user.get("bank_name", ""),
                "bank_account_number": user.get("bank_account_number", ""),
                "wallet_number": user.get("wallet_number", ""),
                "payout_method": user.get("payout_method", "bank"),
                "warnings": safe_list(user.get("warnings")),
            }
        )

        for record_type in ALL_FINANCIAL_RECORD_KEYS:
            for item in safe_list(user.get(record_type)):
                financial_rows.append(
                    {
                        "username": username,
                        "record_type": record_type,
                        "amount": safe_float(item.get("amount", item.get("val", 0))),
                        "note": item.get("note", ""),
                        "record_date": item.get("date", DEFAULT_HIRING_DATE),
                    }
                )

    _delete_all(supabase, "employee_financial_records", "username")
    _delete_all(supabase, "users", "username")

    if user_rows:
        supabase.table("users").insert(user_rows).execute()

    if financial_rows:
        supabase.table("employee_financial_records").insert(financial_rows).execute()


def _write_tasks(supabase: Client, tasks: dict) -> None:
    task_rows = []

    for category, task_list in safe_dict(tasks).items():
        for task_text in safe_list(task_list):
            cleaned = safe_str(task_text).strip()
            if cleaned:
                task_rows.append(
                    {
                        "category": category,
                        "task_text": cleaned,
                    }
                )

    _delete_all(supabase, "tasks", "category")

    if task_rows:
        supabase.table("tasks").insert(task_rows).execute()


def _write_branches(supabase: Client, branches: list) -> None:
    rows = [{"branch_name": item} for item in safe_list(branches) if safe_str(item).strip()]
    _delete_all(supabase, "branches", "branch_name")

    if rows:
        supabase.table("branches").insert(rows).execute()


def _write_expense_categories(supabase: Client, expense_categories: list) -> None:
    rows = [{"category_name": item} for item in safe_list(expense_categories) if safe_str(item).strip()]
    _delete_all(supabase, "expense_categories", "category_name")

    if rows:
        supabase.table("expense_categories").insert(rows).execute()


def _write_printers(supabase: Client, printers: dict) -> None:
    rows = []
    for printer_name, printer_ip in safe_dict(printers).items():
        rows.append(
            {
                "printer_name": printer_name,
                "printer_ip": safe_str(printer_ip),
            }
        )

    _delete_all(supabase, "printers", "printer_name")

    if rows:
        supabase.table("printers").insert(rows).execute()


def _write_history(supabase: Client, history: list) -> None:
    rows = []

    for item in safe_list(history):
        rows.append(
            {
                "report_date": item.get("date", DEFAULT_HIRING_DATE),
                "branch": item.get("branch", ""),
                "shift": item.get("shift", ""),
                "staff": item.get("staff", ""),
                "staff_username": item.get("staff_username", ""),
                "role": item.get("role", ""),
                "job_title": item.get("job_title", ""),
                "report_type": item.get("report_type", ""),
                "sales": safe_float(item.get("sales", 0)),
                "expenses": safe_float(item.get("expenses", 0)),
                "exp_note": item.get("exp_note", ""),
                "diff": safe_float(item.get("diff", 0)),
                "t_open": safe_float(item.get("t_open", 0)),
                "t_close": safe_float(item.get("t_close", 0)),
                "cash_breakdown": safe_dict(item.get("cash_breakdown")),
                "closing_cash_breakdown": safe_dict(item.get("closing_cash_breakdown")),
                "opay_open": safe_float(item.get("opay_open", 0)),
                "opay_close": safe_float(item.get("opay_close", 0)),
                "opay_diff": safe_float(item.get("opay_diff", 0)),
                "debit_open": safe_float(item.get("debit_open", 0)),
                "debit_close": safe_float(item.get("debit_close", 0)),
                "debit_diff": safe_float(item.get("debit_diff", 0)),
                "nbe_open": safe_float(item.get("nbe_open", 0)),
                "nbe_close": safe_float(item.get("nbe_close", 0)),
                "nbe_diff": safe_float(item.get("nbe_diff", 0)),
                "qnb_open": safe_float(item.get("qnb_open", 0)),
                "qnb_close": safe_float(item.get("qnb_close", 0)),
                "qnb_diff": safe_float(item.get("qnb_diff", 0)),
                "fawry_open": safe_float(item.get("fawry_open", 0)),
                "fawry_close": safe_float(item.get("fawry_close", 0)),
                "fawry_diff": safe_float(item.get("fawry_diff", 0)),
                "customer_debts": safe_list(item.get("customer_debts")),
                "printer_diff": safe_dict(item.get("printer_diff")),
                "expenses_list": safe_list(item.get("expenses_list")),
                "social_notes": item.get("social_notes", ""),
                "interaction_notes": item.get("interaction_notes", ""),
                "special_notes": item.get("special_notes", ""),
                "visible_sections": safe_list(item.get("visible_sections")),
            }
        )

    _delete_all(supabase, "shift_history", "staff")

    if rows:
        supabase.table("shift_history").insert(rows).execute()


def _write_training_records(supabase: Client, training_records: dict) -> None:
    rows = []

    for username, item in safe_dict(training_records).items():
        rows.append(
            {
                "username": username,
                "status": item.get("status", "completed"),
                "record_date": item.get("date", DEFAULT_HIRING_DATE),
            }
        )

    _delete_all(supabase, "training_records", "username")

    if rows:
        supabase.table("training_records").insert(rows).execute()


def _write_attendance_records(supabase: Client, attendance_records: dict) -> None:
    try:
        _delete_all(supabase, "attendance_records", "username")
    except Exception:
        return

    rows = []
    for month_key, users_map in safe_dict(attendance_records).items():
        for username, records in safe_dict(users_map).items():
            for item in safe_list(records):
                rows.append(
                    {
                        "month_key": month_key,
                        "username": username,
                        "attendance_date": item.get("date", ""),
                        "attendance_time": item.get("time", ""),
                        "shift": item.get("shift", ""),
                        "late_minutes": int(safe_float(item.get("late_minutes", 0))),
                        "status": item.get("status", ""),
                    }
                )

    if rows:
        supabase.table("attendance_records").insert(rows).execute()


def _write_late_tracking(supabase: Client, late_tracking: dict) -> None:
    try:
        _delete_all(supabase, "late_tracking", "username")
    except Exception:
        return

    rows = []
    for month_key, users_map in safe_dict(late_tracking).items():
        for username, late_count in safe_dict(users_map).items():
            rows.append(
                {
                    "month_key": month_key,
                    "username": username,
                    "late_count": int(safe_float(late_count)),
                }
            )

    if rows:
        supabase.table("late_tracking").insert(rows).execute()


def _write_blocked_users(supabase: Client, blocked_users: dict) -> None:
    try:
        _delete_all(supabase, "blocked_users", "username")
    except Exception:
        return

    rows = []
    for month_key, users_map in safe_dict(blocked_users).items():
        for username, is_blocked in safe_dict(users_map).items():
            rows.append(
                {
                    "month_key": month_key,
                    "username": username,
                    "is_blocked": bool(is_blocked),
                }
            )

    if rows:
        supabase.table("blocked_users").insert(rows).execute()


# =====================================================
# Compatibility full save
# =====================================================
def save_db(data: dict) -> None:
    """
    Transitional compatibility save.
    """
    supabase = get_supabase()

    _upsert_settings(supabase, data)
    _write_users(supabase, data.get("users", {}))
    _write_tasks(supabase, data.get("tasks", {}))
    _write_branches(supabase, data.get("branches", []))
    _write_expense_categories(supabase, data.get("expense_categories", []))
    _write_printers(supabase, data.get("printers", {}))
    _write_history(supabase, data.get("history", []))
    _write_training_records(supabase, data.get("training_records", {}))
    _write_attendance_records(supabase, data.get("attendance_records", {}))
    _write_late_tracking(supabase, data.get("late_tracking", {}))
    _write_blocked_users(supabase, data.get("blocked_users", {}))


# =====================================================
# User helpers
# =====================================================
def create_user(
    username: str,
    password: str,
    full_name: str,
    role: str = "employee",
    job_title: str = "",
) -> tuple[bool, str]:
    db = load_db()

    username = username.strip()
    full_name = full_name.strip()

    if not username:
        return False, "Username is required."

    if not full_name:
        return False, "Full name is required."

    if username in db.get("users", {}):
        return False, "Username already exists."

    new_user = dict(DEFAULT_USER_SCHEMA)
    new_user.update(
        {
            "pass": password,
            "role": role,
            "full_name": full_name,
            "job_title": job_title.strip() or role.replace("_", " ").title(),
            "employee_code": username.upper(),
            "birth_date": DEFAULT_BIRTH_DATE,
            "hiring_date": DEFAULT_HIRING_DATE,
            "salary": 0.0,
            "salary_basic": 0.0,
            "transport_allowance": 0.0,
            "communication_allowance": 0.0,
            "other_allowance": 0.0,
            "bank_name": "",
            "bank_account_number": "",
            "wallet_number": "",
            "payout_method": "bank",
            "warnings": [],
            "bonus": [],
            "deductions": [],
            "overtime": [],
            "extra_leaves": [],
            "advances": [],
            "late_penalties": [],
            "absence_penalties": [],
        }
    )

    db["users"][username] = new_user

    save_db(db)
    return True, "User created successfully."


def get_user_by_username(username: str) -> dict | None:
    db = load_db()
    return db.get("users", {}).get(username)


# =====================================================
# Settings helpers
# =====================================================
def get_manager_phone() -> str:
    db = load_db()
    return safe_str(db.get("manager_phone", DEFAULT_MANAGER_PHONE), DEFAULT_MANAGER_PHONE)
