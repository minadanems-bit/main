# =====================================================
# DATABASE LAYER (SQLITE - PRODUCTION SAFE VERSION)
# =====================================================

import sqlite3
import json
import os


# =====================================================
# SAFE DATABASE LOCATION
# =====================================================

"""
Streamlit Cloud يسمح بالكتابة داخل المشروع فقط.
نخلي قاعدة البيانات داخل نفس المجلد.
"""

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(PROJECT_DIR, "nms_system.db")


# =====================================================
# SAFE CONNECTION FUNCTION
# =====================================================

def get_connection():
    """Return safe sqlite connection"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():
    """
    Create database + default row if not exists.
    Safe for Cloud + Local.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

    cursor.execute("SELECT data FROM app_data WHERE id = 1")
    row = cursor.fetchone()

    if not row:

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


# ✅ Run once at import
init_db()


# =====================================================
# LOAD DATABASE
# =====================================================

def load_db():
    """Load full JSON from SQLite"""

    conn = get_connection()
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
    """Save full JSON safely"""

    conn = get_connection()
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
