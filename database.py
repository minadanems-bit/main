import json
import os
import shutil
from datetime import datetime, date

DB_FILE = 'nms_enterprise_pro_db.json'

# رقم تليفون المدير لإرسال التقارير على واتساب
MANAGER_PHONE = "971522045638"

# الهيكل الافتراضي لقاعدة البيانات
default_structure = {
    "users": {
        "admin": {
            "name": "Administrator",
            "role": "admin",
            "photo": ""
        }
    },
    "branches": ["Main"],
    "tasks": {
        "opening": ["Turn on Machines", "Check Supplies"],
        "closing": ["Clean Area", "Shutdown Systems"],
        "social": ["Post Instagram", "Reply Comments"],
        "interaction": ["Greet Clients", "Follow Up"]
    },
    "expense_categories": ["Maintenance", "Supplies", "Salary"],
    "drafts": {},
    "history": [],
    "logo": ""
}

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return default_structure

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # تحديث تلقائي للحقول الناقصة في أي نسخة قديمة
    for key, value in default_structure.items():
        if key not in data:
            data[key] = value
        elif isinstance(value, dict):
            for subkey, subval in value.items():
                if subkey not in data[key]:
                    data[key][subkey] = subval

    return data

def save_db(data):
    # حفظ الملف الأساسي
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # إنشاء مجلد النسخ الاحتياطية إن لم يكن موجود
    backup_folder = "backups"
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # إنشاء نسخة احتياطية باسم يحتوي على التاريخ والوقت
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.json"
    backup_path = os.path.join(backup_folder, backup_filename)
    shutil.copyfile(DB_FILE, backup_path)
