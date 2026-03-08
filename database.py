# =====================================================
# DATABASE LAYER (SQLITE - FINAL REFACTORED VERSION)
# =====================================================

import json
import os
import sqlite3
from copy import deepcopy
from datetime import datetime

from constants import (
    DEFAULT_APP_DATA,
    DEFAULT_MANAGER_PHONE,
    DEFAULT_TASKS,
    DEFAULT_USER_SCHEMA,
    ROLE_ADMIN,
    ROLE_EMPLOYEE,
    ROLE_OPTIONS,
    TASK_CATEGORIES,
)


# =====================================================
# Paths
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
DB_FILE = os.path.join(DATA_DIR, "nms_system.db")


# =====================================================
# Default Data Schema
# =====================================================
def get_default_data() -> dict:
    return deepcopy(DEFAULT_APP_DATA)


def get_default_user_schema() -> dict:
    return deepcopy(DEFAULT_USER_SCHEMA)


def ensure_directories() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


# =====================================================
# DB Connection
# =====================================================
def get_connection():
    ensure_directories()
    return sqlite3.connect(DB_FILE, check_same_thread=False)


# =====================================================
# Schema Normalization
# =====================================================
def ensure_top_level_defaults(data: dict) -> dict:
    default_data = get_default_data()

    for key, default_value in default_data.items():
        if key not in data:
            data[key] = deepcopy(default_value)

    return data


def ensure_tasks_defaults(data: dict) -> dict:
    data.setdefault("tasks", {})

    for task_category in TASK_CATEGORIES:
        if task_category not in data["tasks"]:
            data["tasks"][task_category] = deepcopy(DEFAULT_TASKS.get(task_category, []))

    return data


def ensure_user_defaults(user: dict) -> dict:
    default_user = get_default_user_schema()

    for key, default_value in default_user.items():
        if key not in user:
            user[key] = deepcopy(default_value)

    if user.get("role") not in ROLE_OPTIONS:
        legacy_role = user.get("role", ROLE_EMPLOYEE)
        user["role"] = ROLE_EMPLOYEE if legacy_role == "user" else ROLE_EMPLOYEE

    if not user.get("job_title"):
        role_value = user.get("role", ROLE_EMPLOYEE)
        user["job_title"] = role_value.replace("_", " ").title()

    return user


def normalize_history_records(data: dict) -> dict:
    history = data.get("history", [])

    for record in history:
        if isinstance(record.get("expenses"), list):
            expenses_list = record.get("expenses", [])
            total_expenses = sum(float(item.get("amount", 0) or 0) for item in expenses_list)

            exp_note = "\n".join(
                f"• {item.get('type', 'Unknown')} : {float(item.get('amount', 0) or 0):,.2f}"
                for item in expenses_list
            ) or "No Expenses Recorded"

            record["expenses_list"] = expenses_list
            record["expenses"] = total_expenses
            record["exp_note"] = record.get("exp_note", exp_note)
        else:
            record.setdefault("expenses_list", [])
            record.setdefault("exp_note", "No Expenses Recorded")

        record.setdefault("shift", "-")
        record.setdefault("staff", "-")
        record.setdefault("staff_username", "")
        record.setdefault("diff", 0.0)
        record.setdefault("t_open", 0.0)
        record.setdefault("t_close", 0.0)
        record.setdefault("cash_breakdown", {})
        record.setdefault("closing_cash_breakdown", {})
        record.setdefault("opay_open", 0.0)
        record.setdefault("opay_close", 0.0)
        record.setdefault("opay_diff", 0.0)
        record.setdefault("debit_open", 0.0)
        record.setdefault("debit_close", 0.0)
        record.setdefault("debit_diff", 0.0)
        record.setdefault("nbe_open", 0.0)
        record.setdefault("nbe_close", 0.0)
        record.setdefault("nbe_diff", 0.0)
        record.setdefault("printer_diff", {})
        record.setdefault("interaction_notes", [])
        record.setdefault("social_notes", [])
        record.setdefault("role", "")

    return data


def normalize_users(data: dict) -> dict:
    users = data.get("users", {})

    for username, user_data in users.items():
        users[username] = ensure_user_defaults(user_data)

        for list_key in ["bonus", "deductions", "overtime", "extra_leaves"]:
            normalized_records = []
            for item in users[username].get(list_key, []):
                normalized_records.append(
                    {
                        "date": item.get("date", ""),
                        "amount": item.get("amount", item.get("val", 0)),
                        "note": item.get("note", ""),
                    }
                )
            users[username][list_key] = normalized_records

    data["users"] = users
    return data


def normalize_data(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}

    data = ensure_top_level_defaults(data)
    data = ensure_tasks_defaults(data)
    data = normalize_users(data)
    data = normalize_history_records(data)

    if "admin" not in data["users"]:
        data["users"]["admin"] = deepcopy(get_default_data()["users"]["admin"])
    else:
        ensure_user_defaults(data["users"]["admin"])
        data["users"]["admin"]["role"] = ROLE_ADMIN
        if not data["users"]["admin"].get("job_title"):
            data["users"]["admin"]["job_title"] = "System Admin"

    return data


# =====================================================
# Initialization
# =====================================================
def init_db() -> None:
    ensure_directories()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
        """
    )

    cursor.execute("SELECT data FROM app_data WHERE id = 1")
    row = cursor.fetchone()

    if not row:
        default_data = get_default_data()
        cursor.execute(
            "INSERT INTO app_data (id, data) VALUES (?, ?)",
            (1, json.dumps(default_data, ensure_ascii=False)),
        )
        conn.commit()

    conn.close()


# =====================================================
# Backup
# =====================================================
def create_backup(data: dict) -> str:
    ensure_directories()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"backup_{timestamp}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return backup_path


def prune_old_backups(max_backups: int = 20) -> None:
    ensure_directories()

    files = [
        os.path.join(BACKUP_DIR, name)
        for name in os.listdir(BACKUP_DIR)
        if name.endswith(".json")
    ]

    files.sort(key=os.path.getmtime, reverse=True)

    for old_file in files[max_backups:]:
        try:
            os.remove(old_file)
        except OSError:
            pass


# =====================================================
# Load / Save
# =====================================================
def load_db() -> dict:
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM app_data WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        data = get_default_data()
        save_db(data, create_backup_file=False)
        return data

    try:
        data = json.loads(row[0])
    except Exception:
        data = get_default_data()
        save_db(data, create_backup_file=False)
        return data

    normalized = normalize_data(data)

    if normalized != data:
        save_db(normalized, create_backup_file=False)

    return normalized


def save_db(data: dict, create_backup_file: bool = True) -> None:
    ensure_directories()

    normalized = normalize_data(data)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO app_data (id, data)
        VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET data = excluded.data
        """,
        (json.dumps(normalized, ensure_ascii=False),),
    )

    conn.commit()
    conn.close()

    if create_backup_file:
        create_backup(normalized)
        prune_old_backups()


# =====================================================
# Utility API
# =====================================================
def get_manager_phone() -> str:
    db = load_db()
    return db.get("manager_phone", DEFAULT_MANAGER_PHONE)


def set_manager_phone(phone: str) -> None:
    db = load_db()
    db["manager_phone"] = phone
    save_db(db)


def username_exists(username: str) -> bool:
    db = load_db()
    return username in db.get("users", {})


def create_user(
    username: str,
    password: str,
    full_name: str,
    role: str = ROLE_EMPLOYEE,
    job_title: str = "",
) -> tuple[bool, str]:
    db = load_db()

    cleaned_username = username.strip()
    cleaned_full_name = full_name.strip()

    if not cleaned_username:
        return False, "Username is required."

    if not cleaned_full_name:
        return False, "Full name is required."

    if cleaned_username in db.get("users", {}):
        return False, "Username already exists."

    if role not in ROLE_OPTIONS:
        role = ROLE_EMPLOYEE

    new_user = get_default_user_schema()
    new_user["pass"] = password
    new_user["full_name"] = cleaned_full_name
    new_user["role"] = role
    new_user["job_title"] = job_title.strip() or role.replace("_", " ").title()

    db.setdefault("users", {})
    db["users"][cleaned_username] = new_user
    save_db(db)

    return True, "User created successfully."


def reset_database() -> None:
    data = get_default_data()
    save_db(data)


# =====================================================
# Boot
# =====================================================
init_db()
