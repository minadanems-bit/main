# =====================================================
# DATABASE LAYER (SUPABASE VERSION)
# =====================================================

import streamlit as st
from supabase import Client, create_client


# =====================================================
# CONNECTION
# =====================================================
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# =====================================================
# HELPERS
# =====================================================
def safe_list(value):
    return value if isinstance(value, list) else []


def safe_dict(value):
    return value if isinstance(value, dict) else {}


def normalize_user_row(row: dict) -> dict:
    return {
        "pass": row.get("password", ""),
        "role": row.get("role", "employee"),
        "full_name": row.get("full_name", row.get("username", "")),
        "photo": row.get("photo"),
        "id_card": row.get("id_card"),
        "phone": row.get("phone", ""),
        "email": row.get("email", ""),
        "national_id": row.get("national_id", ""),
        "address": row.get("address", ""),
        "qualification": row.get("qualification", ""),
        "hiring_date": str(row.get("hiring_date", "2024-01-01")),
        "salary": float(row.get("salary", 0) or 0),
        "bonus": [],
        "deductions": [],
        "overtime": [],
        "extra_leaves": [],
        "job_title": row.get("job_title", ""),
    }


def attach_financial_records(users: dict, financial_rows: list) -> dict:
    for item in financial_rows:
        username = item.get("username")
        if username not in users:
            continue

        record_type = item.get("record_type", "")
        if record_type not in ["bonus", "deductions", "overtime", "extra_leaves"]:
            continue

        users[username].setdefault(record_type, [])
        users[username][record_type].append(
            {
                "date": str(item.get("record_date", "")),
                "amount": float(item.get("amount", 0) or 0),
                "note": item.get("note", ""),
            }
        )

    return users


# =====================================================
# LOAD ALL APP DATA
# =====================================================
def load_db() -> dict:
    supabase = get_supabase()

    # ---------- USERS ----------
    users_result = supabase.table("users").select("*").execute()
    users_rows = users_result.data or []

    users = {}
    for row in users_rows:
        username = row.get("username")
        if username:
            users[username] = normalize_user_row(row)

    # ---------- FINANCIAL RECORDS ----------
    fin_result = supabase.table("employee_financial_records").select("*").execute()
    fin_rows = fin_result.data or []
    users = attach_financial_records(users, fin_rows)

    # ---------- TASKS ----------
    tasks_result = supabase.table("tasks").select("*").execute()
    tasks_rows = tasks_result.data or []

    tasks = {
        "opening": [],
        "closing": [],
        "social": [],
        "interaction": [],
        "cleaning": [],
        "design": [],
    }

    for row in tasks_rows:
        category = row.get("category", "")
        task_text = row.get("task_text", "")
        if category in tasks and task_text:
            tasks[category].append(task_text)

    # ---------- BRANCHES ----------
    branches_result = supabase.table("branches").select("*").execute()
    branches_rows = branches_result.data or []
    branches = [row.get("branch_name", "") for row in branches_rows if row.get("branch_name")]

    # ---------- EXPENSE CATEGORIES ----------
    expense_result = supabase.table("expense_categories").select("*").execute()
    expense_rows = expense_result.data or []
    expense_categories = [
        row.get("category_name", "")
        for row in expense_rows
        if row.get("category_name")
    ]

    # ---------- PRINTERS ----------
    printers_result = supabase.table("printers").select("*").execute()
    printers_rows = printers_result.data or []
    printers = {
        row.get("printer_name", ""): row.get("printer_ip", "")
        for row in printers_rows
        if row.get("printer_name")
    }

    # ---------- HISTORY ----------
    history_result = supabase.table("shift_history").select("*").order("created_at").execute()
    history_rows = history_result.data or []

    history = []
    for row in history_rows:
        history.append(
            {
                "date": str(row.get("report_date", "")),
                "branch": row.get("branch", ""),
                "shift": row.get("shift", ""),
                "staff": row.get("staff", ""),
                "staff_username": row.get("staff_username", ""),
                "role": row.get("role", ""),
                "job_title": row.get("job_title", ""),
                "report_type": row.get("report_type", ""),
                "sales": float(row.get("sales", 0) or 0),
                "expenses": float(row.get("expenses", 0) or 0),
                "expenses_list": safe_list(row.get("expenses_list")),
                "exp_note": row.get("exp_note", ""),
                "diff": float(row.get("diff", 0) or 0),
                "t_open": float(row.get("t_open", 0) or 0),
                "t_close": float(row.get("t_close", 0) or 0),
                "cash_breakdown": safe_dict(row.get("cash_breakdown")),
                "closing_cash_breakdown": safe_dict(row.get("closing_cash_breakdown")),
                "opay_open": float(row.get("opay_open", 0) or 0),
                "opay_close": float(row.get("opay_close", 0) or 0),
                "opay_diff": float(row.get("opay_diff", 0) or 0),
                "debit_open": float(row.get("debit_open", 0) or 0),
                "debit_close": float(row.get("debit_close", 0) or 0),
                "debit_diff": float(row.get("debit_diff", 0) or 0),
                "nbe_open": float(row.get("nbe_open", 0) or 0),
                "nbe_close": float(row.get("nbe_close", 0) or 0),
                "nbe_diff": float(row.get("nbe_diff", 0) or 0),
                "printer_diff": safe_dict(row.get("printer_diff")),
                "social_notes": row.get("social_notes", ""),
                "interaction_notes": row.get("interaction_notes", ""),
                "special_notes": row.get("special_notes", ""),
                "visible_sections": safe_list(row.get("visible_sections")),
            }
        )

    # ---------- TRAINING RECORDS ----------
    training_result = supabase.table("training_records").select("*").execute()
    training_rows = training_result.data or []

    training_records = {}
    for row in training_rows:
        username = row.get("username")
        if username:
            training_records[username] = {
                "date": str(row.get("record_date", "")),
                "status": row.get("status", "completed"),
            }

    # ---------- SETTINGS ----------
    settings_result = supabase.table("app_settings").select("*").execute()
    settings_rows = settings_result.data or []

    settings_map = {}
    for row in settings_rows:
        settings_map[row.get("setting_key")] = row.get("setting_value")

    manager_phone = settings_map.get("manager_phone", "201234567890")
    logo = settings_map.get("logo", None)

    return {
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
    }


# =====================================================
# SAVE FULL APP DATA
# =====================================================
def save_db(data: dict) -> None:
    supabase = get_supabase()

    # ---------- SETTINGS ----------
    supabase.table("app_settings").upsert(
        [
            {"setting_key": "manager_phone", "setting_value": data.get("manager_phone", "201234567890")},
            {"setting_key": "logo", "setting_value": data.get("logo", None)},
        ],
        on_conflict="setting_key",
    ).execute()

    # ---------- USERS ----------
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

    supabase.table("users").delete().neq("username", "__never__").execute()
    if user_rows:
        supabase.table("users").insert(user_rows).execute()

    supabase.table("employee_financial_records").delete().neq("username", "__never__").execute()
    if financial_rows:
        supabase.table("employee_financial_records").insert(financial_rows).execute()

    # ---------- TASKS ----------
    task_rows = []
    tasks = safe_dict(data.get("tasks"))
    for category, task_list in tasks.items():
        for task_text in safe_list(task_list):
            task_rows.append({"category": category, "task_text": task_text})

    supabase.table("tasks").delete().neq("category", "__never__").execute()
    if task_rows:
        supabase.table("tasks").insert(task_rows).execute()

    # ---------- BRANCHES ----------
    branch_rows = [{"branch_name": item} for item in safe_list(data.get("branches")) if str(item).strip()]
    supabase.table("branches").delete().neq("branch_name", "__never__").execute()
    if branch_rows:
        supabase.table("branches").insert(branch_rows).execute()

    # ---------- EXPENSE CATEGORIES ----------
    expense_rows = [
        {"category_name": item}
        for item in safe_list(data.get("expense_categories"))
        if str(item).strip()
    ]
    supabase.table("expense_categories").delete().neq("category_name", "__never__").execute()
    if expense_rows:
        supabase.table("expense_categories").insert(expense_rows).execute()

    # ---------- PRINTERS ----------
    printer_rows = []
    for printer_name, printer_ip in safe_dict(data.get("printers")).items():
        printer_rows.append(
            {
                "printer_name": printer_name,
                "printer_ip": printer_ip,
            }
        )

    supabase.table("printers").delete().neq("printer_name", "__never__").execute()
    if printer_rows:
        supabase.table("printers").insert(printer_rows).execute()

    # ---------- HISTORY ----------
    history_rows = []
    for item in safe_list(data.get("history")):
        history_rows.append(
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

    supabase.table("shift_history").delete().neq("staff", "__never__").execute()
    if history_rows:
        supabase.table("shift_history").insert(history_rows).execute()

    # ---------- TRAINING ----------
    training_rows = []
    for username, item in safe_dict(data.get("training_records")).items():
        training_rows.append(
            {
                "username": username,
                "status": item.get("status", "completed"),
                "record_date": item.get("date", "2024-01-01"),
            }
        )

    supabase.table("training_records").delete().neq("username", "__never__").execute()
    if training_rows:
        supabase.table("training_records").insert(training_rows).execute()


# =====================================================
# USER HELPERS
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

    db["users"][username] = {
        "pass": password,
        "role": role,
        "full_name": full_name,
        "photo": None,
        "id_card": None,
        "phone": "",
        "email": "",
        "national_id": "",
        "address": "",
        "qualification": "",
        "hiring_date": "2024-01-01",
        "salary": 0.0,
        "bonus": [],
        "deductions": [],
        "overtime": [],
        "extra_leaves": [],
        "job_title": job_title.strip() or role.replace("_", " ").title(),
    }

    save_db(db)
    return True, "User created successfully."


# =====================================================
# SETTINGS HELPERS
# =====================================================
def get_manager_phone() -> str:
    db = load_db()
    return str(db.get("manager_phone", "201234567890"))
