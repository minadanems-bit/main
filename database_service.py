# database_service.py
import sqlite3
import json
from datetime import date

DB_FILE = "/tmp/nms_system.db"  # safe for Streamlit Cloud /tmp

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)
    cur.execute("SELECT data FROM app_data WHERE id = 1")
    row = cur.fetchone()
    if not row:
        default = {
            "logo": None,
            "manager_phone": "+971522045638",
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
            "tasks": {"opening": [], "closing": [], "social": [], "interaction": []},
            "history": [],
            "drafts": {},
            "logs": [],
            "printers": {
                "Kyocera 3010i": "192.168.1.120",
                "Xerox 7835": "192.168.1.65",
                "Kyocera P5031DN": "192.168.1.126",
                "Print N' Go": "192.168.1.130"
            }
        }
        cur.execute("INSERT INTO app_data (id, data) VALUES (?, ?)", (1, json.dumps(default, ensure_ascii=False)))
        conn.commit()
    conn.close()

# call once on import to ensure DB exists
init_db()

def load_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT data FROM app_data WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception:
            return {}
    return {}

def save_db(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE app_data SET data = ? WHERE id = 1", (json.dumps(data, ensure_ascii=False),))
    conn.commit()
    conn.close()

def get_manager_phone():
    db = load_db()
    return db.get("manager_phone", "+971522045638")
