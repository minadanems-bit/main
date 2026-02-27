# =====================================================
# PRINTER SERVICE (FINAL STABLE VERSION)
# =====================================================

import streamlit as st
from database import load_db, save_db

# =====================================================
# DATABASE INIT
# =====================================================

def init_printers():
    db = load_db()

    if "printers" not in db:
        db["printers"] = {
            "Kyocera 3010i": "192.168.1.120",
            "Xerox 7835": "192.168.1.65",
            "Kyocera P5031DN": "192.168.1.126"
        }
        save_db(db)

init_printers()


# =====================================================
# GET PRINTERS (RETURNS DICT)
# =====================================================

def get_printers():
    db = load_db()
    return db.get("printers", {})


# =====================================================
# CALCULATE DIFFERENCE
# =====================================================

def calculate_printer_difference(start_data, end_data):

    diff = {}

    if not start_data or not end_data:
        return diff

    for printer in start_data:

        diff[printer] = {}

        fields = ["Total", "One Side", "Two Side", "Errors", "Jam"]

        for field in fields:
            try:
                start_val = int(start_data.get(printer, {}).get(field, 0) or 0)
                end_val = int(end_data.get(printer, {}).get(field, 0) or 0)
                diff[printer][field] = end_val - start_val
            except:
                diff[printer][field] = 0

    return diff


# =====================================================
# PRINTER MANAGEMENT UI  ✅ (THIS WAS MISSING)
# =====================================================

def printer_management_ui(db):

    st.title("🖨 Printer Management")

    if "printers" not in db:
        db["printers"] = {}

    st.subheader("📋 Current Printers")

    for name, ip in db["printers"].items():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**{name}** — {ip}")

        with col2:
            if st.button("❌ Delete", key=f"del_{name}"):
                del db["printers"][name]
                save_db(db)
                st.rerun()

    st.divider()

    st.subheader("➕ Add New Printer")

    new_name = st.text_input("Printer Name")
    new_ip = st.text_input("Printer IP")

    if st.button("Add Printer", use_container_width=True):

        if new_name and new_ip:
            db["printers"][new_name] = new_ip
            save_db(db)
            st.success("Printer Added ✅")
            st.rerun()
        else:
            st.warning("Enter Name and IP")


# =====================================================
# SHIFT INPUT TAB (USED IF NEEDED)
# =====================================================

def printer_shift_tab(title, key_prefix):

    st.markdown(f"## {title}")

    printer_data = {}

    printers = get_printers()

    for printer in printers.keys():

        st.markdown(f"### 📠 {printer}")

        base_key = f"{key_prefix}_{printer}"

        total = st.number_input("✔ Total", min_value=0, key=f"{base_key}_total")
        one = st.number_input("✔ 1 Side", min_value=0, key=f"{base_key}_one")
        two = st.number_input("✔ 2 Side", min_value=0, key=f"{base_key}_two")
        errors = st.number_input("❌ Errors", min_value=0, key=f"{base_key}_errors")
        jam = st.number_input("⚠ Jam", min_value=0, key=f"{base_key}_jam")

        printer_data[printer] = {
            "Total": total,
            "One Side": one,
            "Two Side": two,
            "Errors": errors,
            "Jam": jam
        }

        st.divider()

    return printer_data


# =====================================================
# OPTIONAL FULL SHIFT COMPARISON PAGE
# =====================================================

def printer_shift_comparison():

    st.subheader("📊 Printer Shift Control")

    tab1, tab2 = st.tabs(["🔵 Start Shift", "🔴 End Shift"])

    with tab1:
        start_data = printer_shift_tab("Start Counters", "start")

    with tab2:
        end_data = printer_shift_tab("End Counters", "end")

    st.divider()

    if st.button("📈 Calculate Difference", use_container_width=True):

        diff = calculate_printer_difference(start_data, end_data)

        st.session_state["printer_start"] = start_data
        st.session_state["printer_end"] = end_data
        st.session_state["printer_diff"] = diff

        st.success("Calculated Successfully ✅")

        for printer, values in diff.items():

            st.markdown(f"### 📠 {printer}")

            col1, col2, col3 = st.columns(3)

            col1.metric("Total", values.get("Total", 0))
            col2.metric("1 Side", values.get("One Side", 0))
            col3.metric("2 Side", values.get("Two Side", 0))

            col4, col5 = st.columns(2)

            col4.metric("Errors", values.get("Errors", 0))
            col5.metric("Jam", values.get("Jam", 0))

            st.divider()
