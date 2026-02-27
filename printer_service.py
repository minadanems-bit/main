# ===============================
# PRINTER SERVICE
# ===============================

import streamlit as st
from database import load_db, save_db

# ===============================
# DATABASE INITIALIZATION
# ===============================

db = load_db()

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
# 🖨 PRINTER MANAGEMENT UI (ADMIN PANEL)
# =====================================================

def printer_management_ui(db):

    st.subheader("🖨 Printer Management")

    printers = db.get("printers", {})

    for name, ip in list(printers.items()):

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

                printers.pop(name, None)
                db["printers"] = printers
                save_db(db)
                st.rerun()

        if st.button("💾 Update", key=f"update_{name}"):

            printers.pop(name, None)
            printers[new_name] = new_ip

            db["printers"] = printers
            save_db(db)

            st.success("✅ Printer Updated!")
            st.rerun()

        st.divider()

    # ===============================
    # ➕ Add New Printer
    # ===============================

    st.subheader("➕ Add New Printer")

    p_name = st.text_input("Printer Name", key="add_printer_name")
    p_ip = st.text_input("Printer IP", key="add_printer_ip")

    if st.button("Add Printer"):

        if p_name and p_ip:

            printers[p_name] = p_ip
            db["printers"] = printers
            save_db(db)

            st.success("✅ Printer Added!")
            st.rerun()


# =====================================================
# 🖨 SHIFT COUNTER MODULE (TAB 1 & TAB 2)
# =====================================================

def printer_shift_tab(title, key_prefix):

    st.markdown(f"## {title}")

    printer_data = {}

    for printer in PRINTERS:

        st.markdown(f"### 📠 {printer}")

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        col5 = st.columns(1)

        with col1:
            total = st.number_input(
                "Total",
                min_value=0,
                key=f"{key_prefix}_{printer}_total"
            )

        with col2:
            one_side = st.number_input(
                "1 Side",
                min_value=0,
                key=f"{key_prefix}_{printer}_one"
            )

        with col3:
            two_side = st.number_input(
                "2 Side",
                min_value=0,
                key=f"{key_prefix}_{printer}_two"
            )

        with col4:
            errors = st.number_input(
                "Errors",
                min_value=0,
                key=f"{key_prefix}_{printer}_errors"
            )

        with col5:
            jam = st.number_input(
                "Jam",
                min_value=0,
                key=f"{key_prefix}_{printer}_jam"
            )

        printer_data[printer] = {
            "Total": total,
            "One Side": one_side,
            "Two Side": two_side,
            "Errors": errors,
            "Jam": jam
        }

        st.divider()

    return printer_data


# =====================================================
# 🟢 MAIN SHIFT COMPARISON (TAB 1 + TAB 2 DIFFERENCE)
# =====================================================

def printer_shift_comparison():

    st.subheader("📊 Printer Shift Comparison")

    st.write("### 🔵 Start Shift")

    start_data = printer_shift_tab("Start Counters", "start")

    st.write("### 🔴 End Shift")

    end_data = printer_shift_tab("End Counters", "end")

    if st.button("📈 Calculate Difference"):

        diff = calculate_printer_difference(start_data, end_data)

        st.success("✅ Difference Calculated")

        st.json(diff)

        st.session_state["printer_start"] = start_data
        st.session_state["printer_end"] = end_data
        st.session_state["printer_diff"] = diff
