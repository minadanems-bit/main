# =====================================================
# DATABASE LAYER (SQLITE - REFACTORED VERSION)
# =====================================================

import json
import os
import shutil
import sqlite3
from datetime import datetime


# =====================================================
# Paths & Constants
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
DB_FILE = os.path.join(DATA_DIR, "nms_system.db")

DEFAULT_MANAGER_PHONE = "+971522045638"


# =====================================================
# Default Data Schema
# =====================================================
def get_default_data() -> dict:
    return {
        "logo": None,
        "manager_phone": DEFAULT_MANAGER_PHONE,
        "branches": [],
        "expense_categories": [],
        "users": {
            "admin": {
                "pass": "admin123",
                "role": "admin",
                "full_name": "Manager",
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
            }
        },
        "tasks": {
            "opening": [],
            "closing": [],
            "social": [],
            "interaction": [],
        },
        "history": [],
        "drafts": {},
        "logs": [],
        "printers": {
            "Kyocera 3010i": "192.168.1.120",
            "Xerox 7835": "192.168.1.65",
            "Kyocera P5031DN": "192.168.1.126",
        },
        "training_records": {},
    }


def ensure_directories() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


# =====================================================
# DB Connection
# =====================================================
def get_connection():
    ensure_directories()
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn


# =====================================================
# Schema Normalization
# =====================================================
def ensure_top_level_defaults(data: dict) -> dict:
    default_data = get_default_data()

    for key, default_value in default_data.items():
        if key not in data:
            data[key] = default_value

    return data


def ensure_user_defaults(user: dict) -> dict:
    default_user = {
        "pass": "",
        "role": "user",
        "full_name": "",
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
    }

    for key, default_value in default_user.items():
        if key not in user:
            user[key] = default_value

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

        record.setdefault("diff", 0.0)
        record.setdefault("t_open", 0.0)
        record.setdefault("t_close", 0.0)
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
    data = normalize_users(data)
    data = normalize_history_records(data)

    if "admin" not in data["users"]:
        data["users"]["admin"] = get_default_data()["users"]["admin"]
    else:
        ensure_user_defaults(data["users"]["admin"])
        data["users"]["admin"]["role"] = "admin"

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


def reset_database() -> None:
    data = get_default_data()
    save_db(data)


# =====================================================
# Boot
# =====================================================
init_db()
