# =====================================================
# DATABASE LAYER (SQLITE - PRODUCTION SAFE VERSION V2)
# =====================================================

import sqlite3
import json
import os
import threading

# =====================================================
# SAFE DATABASE LOCATION
# =====================================================

import os

# ✅ Cloud Safe Storage
if os.path.exists("/mount"):
    BASE_DIR = "/mount/data"
else:
    BASE_DIR = os.path.join(os.getcwd(), "data")

os.makedirs(BASE_DIR, exist_ok=True)

DB_FILE = os.path.join(BASE_DIR, "nms_system.db")

print("📂 DATABASE FILE:", DB_FILE)

# Lock لحماية الكتابة من التداخل
db_lock = threading.Lock()


# =====================================================
# CONNECTION
# =====================================================

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():

    with db_lock:
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


# Run once
init_db()


# =====================================================
# LOAD DATABASE (SAFE)
# =====================================================

def load_db():

    with db_lock:

        if not os.path.exists(DB_FILE):
            init_db()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM app_data WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            try:
                return json.loads(row[0])
            except Exception as e:
                print("❌ DATABASE JSON ERROR:", e)
                return {}

        return {}


# =====================================================
# SAVE DATABASE (SAFE + ATOMIC STYLE)
# =====================================================

def save_db(data):

    with db_lock:

        temp_data = json.dumps(data, ensure_ascii=False)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE app_data SET data = ? WHERE id = 1",
            (temp_data,)
        )

        conn.commit()
        conn.close()


# =====================================================
# GET MANAGER PHONE
# =====================================================

def get_manager_phone():
    db = load_db()
    return db.get("manager_phone", "201234567890")
