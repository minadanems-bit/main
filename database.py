
# =====================================================
# DATABASE LAYER (OFFLINE SQLITE VERSION)
# =====================================================

import os
import sqlite3
import json
from datetime import datetime

from constants import DEFAULT_APP_DATA, DEFAULT_USER_SCHEMA

DB_FOLDER = "local_data"
DB_FILE = os.path.join(DB_FOLDER, "nms_erp.db")


# =====================================================
# Connection
# =====================================================

def get_connection():
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# Init database
# =====================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_state (
        id INTEGER PRIMARY KEY,
        data TEXT
    )
    """)

    conn.commit()
    conn.close()


# =====================================================
# Load DB
# =====================================================

def load_db():

    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM app_state WHERE id=1")
    row = cursor.fetchone()

    if not row:
        data = DEFAULT_APP_DATA

        cursor.execute(
            "INSERT INTO app_state (id, data) VALUES (1, ?)",
            (json.dumps(data),)
        )

        conn.commit()
        conn.close()

        return data

    conn.close()

    return json.loads(row["data"])


# =====================================================
# Save DB
# =====================================================

def save_db(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE app_state SET data=? WHERE id=1",
        (json.dumps(data),)
    )

    conn.commit()
    conn.close()


# =====================================================
# User Helpers
# =====================================================

def create_user(username, password, full_name, role="employee", job_title=""):

    db = load_db()

    if username in db["users"]:
        return False, "Username already exists"

    user = DEFAULT_USER_SCHEMA.copy()

    user.update({
        "pass": password,
        "role": role,
        "full_name": full_name,
        "job_title": job_title,
    })

    db["users"][username] = user

    save_db(db)

    return True, "User created successfully"


def get_user_by_username(username):

    db = load_db()

    return db["users"].get(username)


# =====================================================
# Drafts
# =====================================================

def save_user_draft(username, draft_data):

    db = load_db()

    db["drafts"][username] = draft_data

    save_db(db)

    return True, "Draft saved"


def load_user_draft(username):

    db = load_db()

    return db["drafts"].get(username, {})


# =====================================================
# Attendance
# =====================================================

def insert_attendance_record(payload):

    db = load_db()

    month_key = payload.get("month_key")
    username = payload.get("username")

    db["attendance_records"].setdefault(month_key, {})
    db["attendance_records"][month_key].setdefault(username, [])

    db["attendance_records"][month_key][username].append(payload)

    save_db(db)

    return True, "Attendance inserted"


# =====================================================
# Late tracking
# =====================================================

def upsert_late_tracking(month_key, username, late_count):

    db = load_db()

    db["late_tracking"].setdefault(month_key, {})
    db["late_tracking"][month_key][username] = late_count

    save_db(db)

    return True, "Late tracking updated"


# =====================================================
# Blocked users
# =====================================================

def upsert_blocked_user(month_key, username, is_blocked):

    db = load_db()

    db["blocked_users"].setdefault(month_key, {})
    db["blocked_users"][month_key][username] = is_blocked

    save_db(db)

    return True, "Blocked user updated"
