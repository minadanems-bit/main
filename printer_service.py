# ===============================
# PRINTER SERVICE
# ===============================

from database import load_db, save_db

# تحميل قاعدة البيانات
db = load_db()

# ===============================
# PRINTER CONFIG
# ===============================

if "printers" not in db:
    db["printers"] = {
        "Kyocera 3010i": "192.168.1.120",
        "Xerox 7835": "192.168.1.65",
        "Kyocera P5031DN": "192.168.1.126"
    }
    save_db(db)

PRINTERS = db.get("printers", {})


# =====================================================
# CALCULATE PRINTER DIFFERENCE
# =====================================================

def calculate_printer_difference(start_data, end_data):
    """
    حساب الفرق بين عدادات بداية الشفت ونهايته
    """

    diff = {}

    if not start_data or not end_data:
        return diff

    for printer in start_data:

        diff[printer] = {}

        fields = ["Total", "One Side", "Two Side", "Errors", "Jam"]

        for field in fields:
            try:
                start_value = int(start_data[printer].get(field, 0) or 0)
                end_value = int(end_data.get(printer, {}).get(field, 0) or 0)

                diff[printer][field] = end_value - start_value

            except:
                diff[printer][field] = 0

    return diff
