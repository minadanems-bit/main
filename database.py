# =====================================================
# DATABASE LAYER (CLOUD SAFE VERSION - STABLE)
# =====================================================

import sqlite3
import json
import os

# =====================================================
# ✅ Safe Path for Streamlit Cloud
# =====================================================

# /tmp أفضل مكان للكتابة على Cloud
DB_FILE = os.path.join("/tmp", "nms_system.db")

print("📂 DATABASE FILE:", DB_FILE)


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():
    """
    Create database + table + default row if not exists.
    Won't overwrite existing data.
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

    # Check if system row exists
    cursor.execute("SELECT data FROM app_data WHERE id = 1")
    row = cursor.fetchone()

    if not row:
        print("🚀 Creating Fresh Database With Default Data")

        default_data = {
            "logo": None,
            "manager_phone": "971522045638",

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
            (1, json.dumps(default_data, ensure_ascii=False))
        )

        conn.commit()

    conn.close()


# =====================================================
# RUN ONCE
# =====================================================

init_db()


# =====================================================
# LOAD DATABASE
# =====================================================

def load_db():
    """Load full JSON safely"""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM app_data WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception as e:
            print("❌ JSON ERROR:", e)
            return {}

    return {}


# =====================================================
# SAVE DATABASE
# =====================================================

def save_db(data):
    """Save full system state safely"""

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
    return db.get("manager_phone", "971522045638")
