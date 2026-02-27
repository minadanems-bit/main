# ===============================
# PRINTER SERVICE
# ===============================

import streamlit as st
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


# =====================================================
# 🖨 PRINTER MANAGEMENT UI
# =====================================================

def printer_management_ui():

    st.subheader("🖨 Manage Printers")

    global PRINTERS
    db_local = load_db()
    PRINTERS = db_local.get("printers", {})

    # عرض الطابعات الحالية
    for name, ip in list(PRINTERS.items()):

        st.markdown(f"### 📠 {name}")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            new_name = st.text_input(
                "Printer Name",
                value=name,
                key=f"name_{name}"
            )

        with col2:
            new_ip = st.text_input(
                "IP Address",
                value=ip,
                key=f"ip_{name}"
            )

        with col3:
            if st.button("❌ Delete", key=f"del_{name}"):

                PRINTERS.pop(name, None)
                db_local["printers"] = PRINTERS
                save_db(db_local)

                st.warning("Printer Deleted")
                st.rerun()

        if st.button("💾 Update Printer", key=f"update_{name}"):

            # حذف القديم
            if name in PRINTERS:
                PRINTERS.pop(name)

            # إضافة الجديد
            PRINTERS[new_name] = new_ip

            db_local["printers"] = PRINTERS
            save_db(db_local)

            st.success("✅ Printer Updated!")
            st.rerun()

        st.divider()

    # ===============================
    # ➕ إضافة طابعة جديدة
    # ===============================

    st.subheader("➕ Add New Printer")

    p_name = st.text_input("Printer Name", key="add_printer_name")
    p_ip = st.text_input("Printer IP", key="add_printer_ip")

    if st.button("Add Printer"):

        if p_name and p_ip:

            PRINTERS[p_name] = p_ip
            db_local["printers"] = PRINTERS
            save_db(db_local)

            st.success("✅ Printer Added!")
            st.rerun()
