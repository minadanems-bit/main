# =====================================================
# DATABASE LAYER (JSON FILE VERSION)
# =====================================================

import json
import os

# ملف الجيسون هيبقى جوه المشروع
DB_FILE = "nms_enterprise_pro_db.json"


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():

    if not os.path.exists(DB_FILE):

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

        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)


init_db()


# =====================================================
# LOAD
# =====================================================

def load_db():

    if not os.path.exists(DB_FILE):
        init_db()

    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================
# SAVE
# =====================================================

def save_db(data):

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =====================================================
# GET MANAGER PHONE
# =====================================================

def get_manager_phone():
    db = load_db()
    return db.get("manager_phone", "201234567890")
مفيش موظفين ولا مهام ولا اى حاجة انا سجلتها ، لية ؟
