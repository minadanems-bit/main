# =====================================================
# DATABASE LAYER (SQLITE - JSON STORAGE MODE)
# =====================================================

import sqlite3
import json

DB_FILE = "nms_system.db"   # 👈 اسم ملف قاعدة البيانات الجديد


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM app_data")
    count = cursor.fetchone()[0]

    if count == 0:
        default_data = {
            "logo": None,
            "manager_phone": "201234567890",
            "branches": [],
            "expense_categories": [],
            "users": {},
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
            "INSERT INTO app_data (id, data) VALUES (1, ?)",
            (json.dumps(default_data),)
        )

    conn.commit()
    conn.close()


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
        return json.loads(row[0])

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
