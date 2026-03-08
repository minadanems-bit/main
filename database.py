# =====================================================
# DATABASE LAYER (JSON FILE VERSION - SAFE PATH)
# =====================================================

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "nms_enterprise_pro_db.json")


def get_default_data():
    return {
        "logo": None,
        "manager_phone": "201234567890",
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
                "salary": 0,
                "bonus": [],
                "deductions": [],
                "overtime": [],
                "extra_leaves": [],
                "job_title": "System Admin",
            }
        },
        "tasks": {
            "opening": [],
            "closing": [],
            "social": [],
            "interaction": [],
            "cleaning": [],
            "design": [],
        },
        "history": [],
        "drafts": {},
        "logs": [],
        "training_records": {},
        "printers": {
            "Kyocera 3010i": "192.168.1.120",
            "Xerox 7835": "192.168.1.65",
            "Kyocera P5031DN": "192.168.1.126",
        },
    }


def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(get_default_data(), f, indent=4, ensure_ascii=False)


def load_db():
    init_db()

    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    default_data = get_default_data()

    for key, value in default_data.items():
        if key not in data:
            data[key] = value
            changed = True

    if "tasks" not in data:
        data["tasks"] = default_data["tasks"]
        changed = True
    else:
        for task_key, task_value in default_data["tasks"].items():
            if task_key not in data["tasks"]:
                data["tasks"][task_key] = task_value
                changed = True

    if "users" not in data:
        data["users"] = default_data["users"]
        changed = True

    for username, user in data["users"].items():
        user_defaults = {
            "pass": "",
            "role": "employee",
            "full_name": "",
            "photo": None,
            "id_card": None,
            "phone": "",
            "email": "",
            "national_id": "",
            "address": "",
            "qualification": "",
            "hiring_date": "2024-01-01",
            "salary": 0,
            "bonus": [],
            "deductions": [],
            "overtime": [],
            "extra_leaves": [],
            "job_title": "",
        }
        for k, v in user_defaults.items():
            if k not in user:
                user[k] = v
                changed = True

    if changed:
        save_db(data)

    return data


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_manager_phone():
    db = load_db()
    return db.get("manager_phone", "201234567890")
