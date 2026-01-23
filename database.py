import json
import os
from datetime import date

DB_FILE = 'nms_enterprise_pro_db.json'

def load_db():
    default_structure = {
        # (حط هنا نفس الديفولت اللي عندك بالكامل)
    }

    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return default_structure

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # (نفس كود التحديث على البيانات القديمة للتأكد من وجود الحقول)

    return data

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
MANAGER_PHONE = "971522045638"
