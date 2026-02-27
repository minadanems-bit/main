# =====================================================
# DATABASE LAYER (SQLITE - JSON STORAGE MODE)
# =====================================================

import sqlite3
import json
import os

DB_FILE = "nms_system.db"


print("DB EXISTS:", os.path.exists(DB_FILE))
# =====================================================
# UTIL: SHOW DB PATH (DEBUG ONLY)
# =====================================================

print("📂 DATABASE PATH:", os.path.abspath(DB_FILE))


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():
    """
    Create database + default row if not exists.
    Safe initialization with full system structure.
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

    # Check if row exists
    cursor.execute("SELECT COUNT(*) FROM app_data WHERE id = 1")
    exists = cursor.fetchone()[0]

    if exists == 0:

        default_data = {
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
                    "salary": 0,
                    "bonus": [],
                    "deductions": [],
                    "overtime": [],
                    "extra_leaves": []
                }
            },

            "tasks": {
                "opening": [],
                "closing": [],
                "social": [],
                "interaction": []
            },

            "history": [],
            "drafts": {},
            "logs": [],
            "printers": {
                "Kyocera 3010i": "192.168.1.120",
                "Xerox 7835": "192.168.1.65",
                "Kyocera P5031DN": "192.168.1.126"
            }
        }

        cursor.execute(
            "INSERT INTO app_data (id, data) VALUES (?, ?)",
            (1, json.dumps(default_data))
        )

        conn.commit()

    conn.close()


# Run once at import
init_db()


# =====================================================
# LOAD DATABASE
# =====================================================

def load_db():
    """
    Load full JSON structure from SQLite.
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM app_data WHERE id = 1")
    row = cursor.fetchone()

    conn.close()

    if row and row[0]:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            print("❌ JSON CORRUPTED — Resetting Database")
            return {}

    return {}


# =====================================================
# SAVE DATABASE
# =====================================================

def save_db(data):
    """
    Save full JSON structure safely.
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE app_data SET data = ? WHERE id = 1",
        (json.dumps(data, ensure_ascii=False),)
    )

    conn.commit()
    conn.close()


# =====================================================
# GET MANAGER PHONE
# =====================================================

def get_manager_phone():
    db = load_db()
    return db.get("manager_phone", "201234567890")
