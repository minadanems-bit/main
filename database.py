# =====================================================
# DATABASE LAYER (SUPABASE VERSION - CLEAN REFACTOR)
# Optimized partial writes + compatibility full save
# =====================================================

from __future__ import annotations

from typing import Any, Callable
import time

import streamlit as st
from httpx import RemoteProtocolError
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
# Financial record keys
# =====================================================
ALL_FINANCIAL_RECORD_KEYS = list(HR_RECORD_KEYS)


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


def _run_with_retry(action: Callable, retries: int = 3, delay: float = 0.6):
    last_error = None
    for attempt in range(retries):
        try:
            return action()
        except RemoteProtocolError as e:
            last_error = e
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
        except Exception as e:
            last_error = e
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
    if last_error:
        raise last_error


def _safe_execute(query, fallback):
    try:
        result = _run_with_retry(lambda: query.execute())
        return result.data or fallback
    except Exception:
        return fallback


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
    rows = _safe_execute(supabase.table("users").select("*"), [])

    users = {}
    for row in rows:
        username = row.get("username")
        if username:
            users[username] = normalize_user_row(row)

    fin_rows = _safe_execute(supabase.table("employee_financial_records").select("*"), [])
    return attach_financial_records(users, fin_rows)


def _load_tasks(supabase: Client) -> dict:
    rows = _safe_execute(supabase.table("tasks").select("*"), [])

    tasks = {category: [] for category in TASK_CATEGORIES}
    for row in rows:
        category = row.get("category", "")
        task_text = row.get("task_text", "")
        if category in tasks and task_text:
            tasks[category].append(task_text)

    return tasks


def _load_branches(supabase: Client) -> list:
    rows = _safe_execute(supabase.table("branches").select("*"), [])
    return [row.get("branch_name", "") for row in rows if row.get("branch_name")]


def _load_expense_categories(supabase: Client) -> list:
    rows = _safe_execute(supabase.table("expense_categories").select("*"), [])
    return [row.get("category_name", "") for row in rows if row.get("category_name")]


def _load_printers(supabase: Client) -> dict:
    rows = _safe_execute(supabase.table("printers").select("*"), [])

    return {
        row.get("printer_name", ""): row.get("printer_ip", "")
        for row in rows
        if row.get("printer_name")
    }


def _load_history(supabase: Client) -> list:
    rows = _safe_execute(
        supabase.table("shift_history").select("*").order("created_at"),
        [],
    )

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
    rows = _safe_execute(supabase.table("training_records").select("*"), [])

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
    rows = _safe_execute(
        supabase.table("attendance_records").select("*").order("created_at"),
        [],
    )

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
                "branch": safe_str(row.get("branch", "")),
                "late_minutes": int(safe_float(row.get("late_minutes", 0))),
                "status": safe_str(row.get("status", "")),
                "created_at": safe_str(row.get("created_at", "")),
            }
        )

    return attendance_records


def _load_late_tracking(supabase: Client) -> dict:
    rows = _safe_execute(supabase.table("late_tracking").select("*"), [])

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
    rows = _safe_execute(supabase.table("blocked_users").select("*"), [])

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
    rows = _safe_execute(supabase.table("app_settings").select("*"), [])

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
    _run_with_retry(
        lambda: supabase.table(table_name).delete().neq(guard_column, "__never__").execute()
    )


def _upsert_settings(supabase: Client, data: dict) -> None:
    logo_value = data.get("logo", "")
    if logo_value is None:
        logo_value = ""

    _run_with_retry(
        lambda: supabase.table("app_settings").upsert(
            [
                {
                    "setting_key": "manager_phone",
                    "setting_value": safe_str(
                        data.get("manager_phone", DEFAULT_MANAGER_PHONE),
                        DEFAULT_MANAGER_PHONE,
                    ),
                },
                {
                    "setting_key": "logo",
                    "setting_value": logo_value,
                },
            ],
            on_conflict="setting_key",
        ).execute()
    )


def _build_user_row(username: str, user: dict) -> dict:
    return {
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


def _build_financial_rows_for_user(username: str, user: dict) -> list[dict]:
    rows = []
    for record_type in ALL_FINANCIAL_RECORD_KEYS:
        for item in safe_list(user.get(record_type)):
            rows.append(
                {
                    "username": username,
                    "record_type": record_type,
                    "amount": safe_float(item.get("amount", item.get("val", 0))),
                    "note": item.get("note", ""),
                    "record_date": item.get("date", DEFAULT_HIRING_DATE),
                }
            )
    return rows


def _write_users(supabase: Client, users: dict) -> None:
    user_rows = []
    financial_rows = []

    for username, user in safe_dict(users).items():
        user_rows.append(_build_user_row(username, user))
        financial_rows.extend(_build_financial_rows_for_user(username, user))

    if user_rows:
        _run_with_retry(
            lambda: supabase.table("users").upsert(user_rows, on_conflict="username").execute()
        )

    _delete_all(supabase, "employee_financial_records", "username")

    if financial_rows:
        _run_with_retry(
            lambda: supabase.table("employee_financial_records").insert(financial_rows).execute()
        )


def _has_any_task_data(tasks: dict) -> bool:
    for task_list in safe_dict(tasks).values():
        for task_text in safe_list(task_list):
            if safe_str(task_text).strip():
                return True
    return False


def _write_tasks(supabase: Client, tasks: dict) -> None:
    if not _has_any_task_data(tasks):
        return

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

    if not task_rows:
        return

    _delete_all(supabase, "tasks", "category")
    _run_with_retry(lambda: supabase.table("tasks").insert(task_rows).execute())


def _write_branches(supabase: Client, branches: list) -> None:
    cleaned_names = []
    seen = set()

    for item in safe_list(branches):
        branch_name = safe_str(item).strip()
        if not branch_name:
            continue
        if branch_name in seen:
            continue
        seen.add(branch_name)
        cleaned_names.append(branch_name)

    rows = [{"branch_name": name} for name in cleaned_names]

    _delete_all(supabase, "branches", "branch_name")

    if rows:
        _run_with_retry(
            lambda: supabase.table("branches").upsert(rows, on_conflict="branch_name").execute()
        )


def _write_expense_categories(supabase: Client, expense_categories: list) -> None:
    cleaned_names = []
    seen = set()

    for item in safe_list(expense_categories):
        category_name = safe_str(item).strip()
        if not category_name:
            continue
        if category_name in seen:
            continue
        seen.add(category_name)
        cleaned_names.append(category_name)

    rows = [{"category_name": name} for name in cleaned_names]

    _delete_all(supabase, "expense_categories", "category_name")

    if rows:
        _run_with_retry(
            lambda: supabase.table("expense_categories").upsert(
                rows,
                on_conflict="category_name",
            ).execute()
        )


def _write_printers(supabase: Client, printers: dict) -> None:
    cleaned_rows = []
    seen = set()

    for printer_name, printer_ip in safe_dict(printers).items():
        name = safe_str(printer_name).strip()
        ip = safe_str(printer_ip).strip()

        if not name:
            continue
        if name in seen:
            continue

        seen.add(name)
        cleaned_rows.append(
            {
                "printer_name": name,
                "printer_ip": ip,
            }
        )

    _delete_all(supabase, "printers", "printer_name")

    if cleaned_rows:
        _run_with_retry(
            lambda: supabase.table("printers").upsert(
                cleaned_rows,
                on_conflict="printer_name",
            ).execute()
        )


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
        _run_with_retry(lambda: supabase.table("shift_history").insert(rows).execute())


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
        _run_with_retry(lambda: supabase.table("training_records").insert(rows).execute())


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
                        "branch": item.get("branch", ""),
                        "late_minutes": int(safe_float(item.get("late_minutes", 0))),
                        "status": item.get("status", ""),
                    }
                )

    if rows:
        _run_with_retry(lambda: supabase.table("attendance_records").insert(rows).execute())


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
        _run_with_retry(lambda: supabase.table("late_tracking").insert(rows).execute())


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
        _run_with_retry(lambda: supabase.table("blocked_users").insert(rows).execute())


# =====================================================
# Compatibility full save
# =====================================================
def save_db(data: dict) -> None:
    """
    Transitional compatibility save.
    IMPORTANT:
    tasks are managed directly by task_service, so we do NOT rewrite tasks here.
    This prevents old in-memory snapshots from deleting tasks unexpectedly.
    """
    supabase = get_supabase()

    _upsert_settings(supabase, data)
    _write_users(supabase, data.get("users", {}))
    _write_branches(supabase, data.get("branches", []))
    _write_expense_categories(supabase, data.get("expense_categories", []))
    _write_printers(supabase, data.get("printers", {}))
    _write_history(supabase, data.get("history", []))
    _write_training_records(supabase, data.get("training_records", {}))
    _write_attendance_records(supabase, data.get("attendance_records", {}))
    _write_late_tracking(supabase, data.get("late_tracking", {}))
    _write_blocked_users(supabase, data.get("blocked_users", {}))


# =====================================================
# Partial write helpers (NEW - for performance)
# =====================================================
def save_user_record(username: str, user: dict) -> tuple[bool, str]:
    try:
        supabase = get_supabase()
        row = _build_user_row(username, user)
        _run_with_retry(
            lambda: supabase.table("users").upsert([row], on_conflict="username").execute()
        )
        return True, "User saved successfully."
    except Exception as e:
        return False, f"Failed to save user: {e}"


def save_user_financial_records(username: str, user: dict) -> tuple[bool, str]:
    try:
        supabase = get_supabase()

        _run_with_retry(
            lambda: supabase.table("employee_financial_records").delete().eq("username", username).execute()
        )

        rows = _build_financial_rows_for_user(username, user)
        if rows:
            _run_with_retry(
                lambda: supabase.table("employee_financial_records").insert(rows).execute()
            )

        return True, "Financial records saved successfully."
    except Exception as e:
        return False, f"Failed to save financial records: {e}"


def insert_attendance_record(payload: dict) -> tuple[bool, str]:
    try:
        supabase = get_supabase()
        _run_with_retry(
            lambda: supabase.table("attendance_records").insert([payload]).execute()
        )
        return True, "Attendance record inserted successfully."
    except Exception as e:
        return False, f"Failed to insert attendance record: {e}"


def upsert_late_tracking(month_key: str, username: str, late_count: int) -> tuple[bool, str]:
    try:
        supabase = get_supabase()
        _run_with_retry(
            lambda: supabase.table("late_tracking").upsert(
                [
                    {
                        "month_key": month_key,
                        "username": username,
                        "late_count": int(late_count),
                    }
                ],
                on_conflict="month_key,username",
            ).execute()
        )
        return True, "Late tracking updated successfully."
    except Exception as e:
        return False, f"Failed to update late tracking: {e}"


def upsert_blocked_user(month_key: str, username: str, is_blocked: bool) -> tuple[bool, str]:
    try:
        supabase = get_supabase()
        _run_with_retry(
            lambda: supabase.table("blocked_users").upsert(
                [
                    {
                        "month_key": month_key,
                        "username": username,
                        "is_blocked": bool(is_blocked),
                    }
                ],
                on_conflict="month_key,username",
            ).execute()
        )
        return True, "Blocked user state updated successfully."
    except Exception as e:
        return False, f"Failed to update blocked user state: {e}"


def save_user_draft(username: str, draft_data: dict) -> tuple[bool, str]:
    """
    يحتاج جدول باسم user_drafts:
    - username text primary key / unique
    - draft_data jsonb
    - updated_at timestamp nullable
    """
    try:
        supabase = get_supabase()
        _run_with_retry(
            lambda: supabase.table("user_drafts").upsert(
                [
                    {
                        "username": username,
                        "draft_data": safe_dict(draft_data),
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ],
                on_conflict="username",
            ).execute()
        )
        return True, "Draft saved successfully."
    except Exception as e:
        return False, f"Failed to save draft: {e}"


def load_user_draft(username: str) -> dict:
    try:
        supabase = get_supabase()
        rows = _safe_execute(
            supabase.table("user_drafts").select("draft_data").eq("username", username).limit(1),
            [],
        )
        if rows:
            return safe_dict(rows[0].get("draft_data"))
        return {}
    except Exception:
        return {}


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
