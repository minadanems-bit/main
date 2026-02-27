# =====================================================
# DATABASE LAYER (SQLITE VERSION)
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

    # ensure single row exists
    cursor.execute("SELECT COUNT(*) FROM app_data")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO app_data (data) VALUES (?)", [json.dumps({})])

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

    if row:
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
        [json.dumps(data)]
    )

    conn.commit()
    conn.close()
