# ===============================
# PRINTER SERVICE (UPDATED VERSION)
# ===============================

import streamlit as st
from database import load_db, save_db

# ===============================
# DATABASE INIT
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
# SHIFT INPUT TAB (FULL DATA — USED IN OPENING & CLOSING)
# =====================================================

def printer_shift_tab(title, key_prefix):

    st.markdown(f"## {title}")

    printer_data = {}

    for printer in PRINTERS:

        st.markdown(f"### 📠 {printer}")

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        col5 = st.columns(1)

        base_key = f"{key_prefix}_{printer}"

        with col1:
            total = st.number_input(
                "✔ Total",
                min_value=0,
                key=f"{base_key}_total"
            )

        with col2:
            one_side = st.number_input(
                "✔ 1 Side",
                min_value=0,
                key=f"{base_key}_one"
            )

        with col3:
            two_side = st.number_input(
                "✔ 2 Side",
                min_value=0,
                key=f"{base_key}_two"
            )

        with col4:
            errors = st.number_input(
                "❌ Errors",
                min_value=0,
                key=f"{base_key}_errors"
            )

        with col5:
            jam = st.number_input(
                "⚠ Jam",
                min_value=0,
                key=f"{base_key}_jam"
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
# SHIFT COMPARISON (TAB 1 & TAB 2 WITH DIFFERENCE)
# =====================================================

def printer_shift_comparison():

    st.subheader("📊 Printer Shift Control")

    tab1, tab2 = st.tabs(["🔵 Start Shift", "🔴 End Shift"])

    # -------- TAB 1 --------
    with tab1:
        st.markdown("### 📥 Start Counters")
        start_data = printer_shift_tab("Start Data", "start")

    # -------- TAB 2 --------
    with tab2:
        st.markdown("### 📤 End Counters")
        end_data = printer_shift_tab("End Data", "end")

    st.divider()

    # -------- CALCULATE --------

    if st.button("📈 Calculate Printer Difference", use_container_width=True):

        diff = calculate_printer_difference(start_data, end_data)

        st.success("✅ Calculated Successfully")

        st.session_state["printer_start"] = start_data
        st.session_state["printer_end"] = end_data
        st.session_state["printer_diff"] = diff

        # ---------------- SHOW TABLE ----------------

        st.markdown("## 📊 Difference Summary")

        for printer, values in diff.items():

            st.markdown(f"### 📠 {printer}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Diff", values.get("Total", 0))

            with col2:
                st.metric("1 Side Diff", values.get("One Side", 0))

            with col3:
                st.metric("2 Side Diff", values.get("Two Side", 0))

            col4, col5 = st.columns(2)

            with col4:
                st.metric("Errors Diff", values.get("Errors", 0))

            with col5:
                st.metric("Jam Diff", values.get("Jam", 0))

            st.divider()
