# =====================================================
# SUPABASE MIGRATION SCRIPT
# Migrates JSON backup data to Supabase
# =====================================================

import json
from pathlib import Path

from supabase import create_client, Client


# =====================================================
# CONFIG
# =====================================================
SUPABASE_URL = "https://undyjopxllbxbfqfrwrt.supabase.co"
SUPABASE_KEY = "sb_publishable_1SD_SMXLvUqA41978CA5Ow_afN4RjVz"

BACKUP_FILE = "backup_2026-03-08_22-44-48.json"


# =====================================================
# CONNECT
# =====================================================
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# =====================================================
# LOAD BACKUP
# =====================================================
def load_backup() -> dict:
    backup_path = Path(BACKUP_FILE)

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {BACKUP_FILE}")

    with open(backup_path, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================
# SAFE HELPERS
# =====================================================
def safe_list(value):
    return value if isinstance(value, list) else []


def safe_dict(value):
    return value if isinstance(value, dict) else {}


def upsert_users(supabase: Client, data: dict) -> None:
    users = safe_dict(data.get("users"))

    payload = []
    for username, user in users.items():
        payload.append(
            {
                "username": username,
                "password": user.get("pass", ""),
                "role": user.get("role", "employee"),
                "full_name": user.get("full_name", username),
                "photo": user.get("photo"),
                "id_card": user.get("id_card"),
                "phone": user.get("phone", ""),
                "email": user.get("email", ""),
                "national_id": user.get("national_id", ""),
                "address": user.get("address", ""),
                "qualification": user.get("qualification", ""),
                "hiring_date": user.get("hiring_date", "2024-01-01"),
                "salary": float(user.get("salary", 0) or 0),
                "job_title": user.get("job_title", ""),
            }
        )

    if payload:
        supabase.table("users").upsert(payload, on_conflict="username").execute()

    financial_rows = []
    for username, user in users.items():
        for record_type in ["bonus", "deductions", "overtime", "extra_leaves"]:
            for item in safe_list(user.get(record_type)):
                financial_rows.append(
                    {
                        "username": username,
                        "record_type": record_type,
                        "amount": float(item.get("amount", item.get("val", 0)) or 0),
                        "note": item.get("note", ""),
                        "record_date": item.get("date", "2024-01-01"),
                    }
                )

    if financial_rows:
        supabase.table("employee_financial_records").insert(financial_rows).execute()


def upsert_tasks(supabase: Client, data: dict) -> None:
    tasks = safe_dict(data.get("tasks"))

    rows = []
    for category, task_list in tasks.items():
        for task_text in safe_list(task_list):
            rows.append(
                {
                    "category": category,
                    "task_text": str(task_text).strip(),
                }
            )

    if rows:
        existing = supabase.table("tasks").select("id").limit(1).execute()
        if not existing.data:
            supabase.table("tasks").insert(rows).execute()


def upsert_branches(supabase: Client, data: dict) -> None:
    rows = [{"branch_name": branch} for branch in safe_list(data.get("branches")) if str(branch).strip()]
    if rows:
        supabase.table("branches").upsert(rows, on_conflict="branch_name").execute()


def upsert_expense_categories(supabase: Client, data: dict) -> None:
    rows = [
        {"category_name": item}
        for item in safe_list(data.get("expense_categories"))
        if str(item).strip()
    ]
    if rows:
        supabase.table("expense_categories").upsert(rows, on_conflict="category_name").execute()


def upsert_printers(supabase: Client, data: dict) -> None:
    printers = safe_dict(data.get("printers"))

    rows = []
    for printer_name, printer_ip in printers.items():
        rows.append(
            {
                "printer_name": printer_name,
                "printer_ip": str(printer_ip),
            }
        )

    if rows:
        supabase.table("printers").upsert(rows, on_conflict="printer_name").execute()


def upsert_history(supabase: Client, data: dict) -> None:
    history = safe_list(data.get("history"))

    rows = []
    for item in history:
        rows.append(
            {
                "report_date": item.get("date", "2024-01-01"),
                "branch": item.get("branch", ""),
                "shift": item.get("shift", ""),
                "staff": item.get("staff", ""),
                "staff_username": item.get("staff_username", ""),
                "role": item.get("role", ""),
                "job_title": item.get("job_title", ""),
                "report_type": item.get("report_type", ""),
                "sales": float(item.get("sales", 0) or 0),
                "expenses": float(item.get("expenses", 0) or 0),
                "exp_note": item.get("exp_note", ""),
                "diff": float(item.get("diff", 0) or 0),
                "t_open": float(item.get("t_open", 0) or 0),
                "t_close": float(item.get("t_close", 0) or 0),
                "cash_breakdown": safe_dict(item.get("cash_breakdown")),
                "closing_cash_breakdown": safe_dict(item.get("closing_cash_breakdown")),
                "opay_open": float(item.get("opay_open", 0) or 0),
                "opay_close": float(item.get("opay_close", 0) or 0),
                "opay_diff": float(item.get("opay_diff", 0) or 0),
                "debit_open": float(item.get("debit_open", 0) or 0),
                "debit_close": float(item.get("debit_close", 0) or 0),
                "debit_diff": float(item.get("debit_diff", 0) or 0),
                "nbe_open": float(item.get("nbe_open", 0) or 0),
                "nbe_close": float(item.get("nbe_close", 0) or 0),
                "nbe_diff": float(item.get("nbe_diff", 0) or 0),
                "printer_diff": safe_dict(item.get("printer_diff")),
                "expenses_list": safe_list(item.get("expenses_list")),
                "social_notes": item.get("social_notes", ""),
                "interaction_notes": item.get("interaction_notes", ""),
                "special_notes": item.get("special_notes", ""),
                "visible_sections": safe_list(item.get("visible_sections")),
            }
        )

    if rows:
        existing = supabase.table("shift_history").select("id").limit(1).execute()
        if not existing.data:
            supabase.table("shift_history").insert(rows).execute()


def upsert_training_records(supabase: Client, data: dict) -> None:
    records = safe_dict(data.get("training_records"))

    rows = []
    for username, item in records.items():
        rows.append(
            {
                "username": username,
                "status": item.get("status", "completed"),
                "record_date": item.get("date", "2024-01-01"),
            }
        )

    if rows:
        supabase.table("training_records").insert(rows).execute()


def upsert_settings(supabase: Client, data: dict) -> None:
    rows = [
        {
            "setting_key": "manager_phone",
            "setting_value": data.get("manager_phone"),
        },
        {
            "setting_key": "logo",
            "setting_value": data.get("logo"),
        },
    ]

    supabase.table("app_settings").upsert(rows, on_conflict="setting_key").execute()


# =====================================================
# RUN
# =====================================================
def migrate() -> None:
    print("Loading backup...")
    data = load_backup()

    print("Connecting to Supabase...")
    supabase = get_supabase()

    print("Migrating users...")
    upsert_users(supabase, data)

    print("Migrating tasks...")
    upsert_tasks(supabase, data)

    print("Migrating branches...")
    upsert_branches(supabase, data)

    print("Migrating expense categories...")
    upsert_expense_categories(supabase, data)

    print("Migrating printers...")
    upsert_printers(supabase, data)

    print("Migrating history...")
    upsert_history(supabase, data)

    print("Migrating training records...")
    upsert_training_records(supabase, data)

    print("Migrating settings...")
    upsert_settings(supabase, data)

    print("Migration completed successfully.")


if __name__ == "__main__":
    migrate()
