# =====================================================
# DATABASE LAYER (SQLITE - STREAMLIT CLOUD SAFE)
# =====================================================

import sqlite3
import json

# ✅ على Streamlit Cloud الأفضل نخزن داخل /tmp
DB_FILE = "/tmp/nms_system.db"

print("📂 DATABASE FILE:", DB_FILE)


# =====================================================
# SAFE CONNECTION
# =====================================================

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():

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

        print("🚀 Creating Fresh Database")

        default_data = {
            "logo": None,
            "manager_phone": "+971522045638",  # ✅ الرقم الجديد

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

    return db.get("manager_phone", "+971522045638")
