# =====================================================
# SUPABASE MIGRATION SCRIPT (RESET + FULL IMPORT)
# =====================================================

import json
from pathlib import Path

from supabase import Client, create_client


# =====================================================
# CONFIG
# =====================================================
SUPABASE_URL = "https://undyjopxllbxbfqfrwrt.supabase.co"
SUPABASE_KEY = "sb_secret_6LUUSrzDDSZcMFF58M6btA_IMGr3Pj8"

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


def chunked(items, size=200):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def count_rows(supabase: Client, table_name: str) -> int:
    result = supabase.table(table_name).select("*", count="exact").limit(1).execute()
    return result.count or 0


def delete_all_rows(supabase: Client, table_name: str, key_column: str) -> None:
    print(f"Clearing table: {table_name}")
    supabase.table(table_name).delete().neq(key_column, "__never__").execute()


def insert_rows(supabase: Client, table_name: str, rows: list, chunk_size: int = 200) -> None:
    if not rows:
        print(f"No rows to insert into {table_name}")
        return

    for batch in chunked(rows, chunk_size):
        supabase.table(table_name).insert(batch).execute()

    print(f"Inserted {len(rows)} rows into {table_name}")


# =====================================================
# BUILD ROWS
# =====================================================
def build_user_rows(data: dict) -> tuple[list, list]:
    users = safe_dict(data.get("users"))
    user_rows = []
    financial_rows = []

    for username, user in users.items():
        user_rows.append(
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

    return user_rows, financial_rows


def build_task_rows(data: dict) -> list:
    tasks = safe_dict(data.get("tasks"))
    rows = []

    for category, task_list in tasks.items():
        for task_text in safe_list(task_list):
            task_text = str(task_text).strip()
            if task_text:
                rows.append(
                    {
                        "category": category,
                        "task_text": task_text,
                    }
                )

    return rows


def build_branch_rows(data: dict) -> list:
    return [
        {"branch_name": branch}
        for branch in safe_list(data.get("branches"))
        if str(branch).strip()
    ]


def build_expense_category_rows(data: dict) -> list:
    return [
        {"category_name": item}
        for item in safe_list(data.get("expense_categories"))
        if str(item).strip()
    ]


def build_printer_rows(data: dict) -> list:
    printers = safe_dict(data.get("printers"))
    rows = []

    for printer_name, printer_ip in printers.items():
        rows.append(
            {
                "printer_name": printer_name,
                "printer_ip": str(printer_ip),
            }
        )

    return rows


def build_history_rows(data: dict) -> list:
    history = safe_list(data.get("history"))
    rows = []

    for item in history:
        interaction_notes = item.get("interaction_notes", "")
        social_notes = item.get("social_notes", "")
        special_notes = item.get("special_notes", "")

        if isinstance(interaction_notes, list):
            interaction_notes = "\n".join(str(x) for x in interaction_notes)
        if isinstance(social_notes, list):
            social_notes = "\n".join(str(x) for x in social_notes)
        if isinstance(special_notes, list):
            special_notes = "\n".join(str(x) for x in special_notes)

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
                "social_notes": social_notes,
                "interaction_notes": interaction_notes,
                "special_notes": special_notes,
                "visible_sections": safe_list(item.get("visible_sections")),
            }
        )

    return rows


def build_training_rows(data: dict) -> list:
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

    return rows


def build_settings_rows(data: dict) -> list:
    return [
        {
            "setting_key": "manager_phone",
            "setting_value": data.get("manager_phone"),
        },
        {
            "setting_key": "logo",
            "setting_value": data.get("logo"),
        },
    ]


# =====================================================
# RUN
# =====================================================
def migrate() -> None:
    print("=" * 60)
    print("Loading backup...")
    data = load_backup()

    print("Connecting to Supabase...")
    supabase = get_supabase()

    # Build rows first
    user_rows, financial_rows = build_user_rows(data)
    task_rows = build_task_rows(data)
    branch_rows = build_branch_rows(data)
    expense_rows = build_expense_category_rows(data)
    printer_rows = build_printer_rows(data)
    history_rows = build_history_rows(data)
    training_rows = build_training_rows(data)
    settings_rows = build_settings_rows(data)

    print("=" * 60)
    print("Prepared data counts:")
    print(f"users: {len(user_rows)}")
    print(f"employee_financial_records: {len(financial_rows)}")
    print(f"tasks: {len(task_rows)}")
    print(f"branches: {len(branch_rows)}")
    print(f"expense_categories: {len(expense_rows)}")
    print(f"printers: {len(printer_rows)}")
    print(f"shift_history: {len(history_rows)}")
    print(f"training_records: {len(training_rows)}")
    print(f"app_settings: {len(settings_rows)}")

    print("=" * 60)
    print("Clearing old data...")

    delete_all_rows(supabase, "employee_financial_records", "username")
    delete_all_rows(supabase, "shift_history", "staff")
    delete_all_rows(supabase, "training_records", "username")
    delete_all_rows(supabase, "tasks", "category")
    delete_all_rows(supabase, "branches", "branch_name")
    delete_all_rows(supabase, "expense_categories", "category_name")
    delete_all_rows(supabase, "printers", "printer_name")
    delete_all_rows(supabase, "users", "username")
    delete_all_rows(supabase, "app_settings", "setting_key")

    print("=" * 60)
    print("Inserting fresh data...")

    insert_rows(supabase, "users", user_rows)
    insert_rows(supabase, "employee_financial_records", financial_rows)
    insert_rows(supabase, "tasks", task_rows)
    insert_rows(supabase, "branches", branch_rows)
    insert_rows(supabase, "expense_categories", expense_rows)
    insert_rows(supabase, "printers", printer_rows)
    insert_rows(supabase, "shift_history", history_rows)
    insert_rows(supabase, "training_records", training_rows)

    if settings_rows:
        supabase.table("app_settings").upsert(settings_rows, on_conflict="setting_key").execute()
        print(f"Upserted {len(settings_rows)} rows into app_settings")

    print("=" * 60)
    print("Final table counts:")
    print(f"users: {count_rows(supabase, 'users')}")
    print(f"employee_financial_records: {count_rows(supabase, 'employee_financial_records')}")
    print(f"tasks: {count_rows(supabase, 'tasks')}")
    print(f"branches: {count_rows(supabase, 'branches')}")
    print(f"expense_categories: {count_rows(supabase, 'expense_categories')}")
    print(f"printers: {count_rows(supabase, 'printers')}")
    print(f"shift_history: {count_rows(supabase, 'shift_history')}")
    print(f"training_records: {count_rows(supabase, 'training_records')}")
    print(f"app_settings: {count_rows(supabase, 'app_settings')}")

    print("=" * 60)
    print("Migration completed successfully.")


if __name__ == "__main__":
    migrate()
