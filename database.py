# =====================================================
# DATABASE LAYER (SQLITE - STREAMLIT SAFE VERSION)
# =====================================================

import sqlite3
import json
import os

# =====================================================
# SAFE STORAGE PATH
# =====================================================

"""
Streamlit Cloud يسمح بالكتابة داخل المشروع فقط.
لذلك نخلي DB داخل نفس المجلد بدون إنشاء فولدر خارجي.
"""

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(PROJECT_DIR, "nms_system.db")

print("📂 DATABASE FILE:", DB_FILE)


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():
    """
    Create database + default row if not exists.
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

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
            (1, json.dumps(default_data, ensure_ascii=False))
        )

        conn.commit()

    conn.close()


# ✅ Run once
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
        except json.JSONDecodeError:
            print("❌ DB JSON CORRUPTED")
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
