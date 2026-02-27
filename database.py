# =====================================================
# DATABASE LAYER (SQLITE VERSION - PRODUCTION SAFE)
# =====================================================

import sqlite3
import json
import os

DB_FILE = "nms_database.db"


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # إنشاء الجدول لو مش موجود
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

    # التحقق هل في row بالفعل
    cursor.execute("SELECT COUNT(*) FROM app_data")
    count = cursor.fetchone()[0]

    if count == 0:

        default_data = {
            "logo": None,
            "manager_phone": "201234567890",
            "branches": ["Main Branch"],
            "expense_categories": [
                "Electricity",
                "Water",
                "Rent"
            ],
            "users": {
                "admin": {
                    "pass": "admin123",
                    "role": "admin",
                    "full_name": "Manager",
                    "phone": "",
                    "salary": 0,
                    "bonus": [],
                    "deductions": [],
                    "overtime": [],
                    "extra_leaves": [],
                    "photo": None
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
            "logs": []
        }

        cursor.execute(
            "INSERT INTO app_data (id, data) VALUES (?, ?)",
            (1, json.dumps(default_data))
        )

    conn.commit()
    conn.close()


# Run once safely
init_db()


# =====================================================
# LOAD DATABASE
# =====================================================

def load_db():

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM app_data WHERE id = 1")
    row = cursor.fetchone()

    conn.close()

    if row and row[0]:
        try:
            return json.loads(row[0])
        except:
            return {}

    return {}


# =====================================================
# SAVE DATABASE
# =====================================================

def save_db(data):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE app_data SET data = ? WHERE id = 1",
        (json.dumps(data),)
    )

    conn.commit()
    conn.close()


# =====================================================
# GET MANAGER PHONE
# =====================================================

def get_manager_phone():

    db = load_db()
    return db.get("manager_phone", "201234567890")
