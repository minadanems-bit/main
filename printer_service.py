# =====================================================
# PRINTER SERVICE (FINAL PRO VERSION)
# =====================================================

import streamlit as st
from database import load_db, save_db

# =====================================================
# INITIALIZE DEFAULT PRINTERS
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
# GET PRINTERS
# =====================================================

def get_printers():
    db = load_db()
    return db.get("printers", {})

# =====================================================
# CALCULATE DIFFERENCE
# =====================================================

def calculate_printer_difference(start_data, end_data):

    diff = {}

    printers = set(start_data.keys()) | set(end_data.keys())

    fields = ["Total", "One Side", "Two Side", "Errors", "Jam"]

    for printer in printers:

        diff[printer] = {}

        for field in fields:

            start_val = start_data.get(printer, {}).get(field, 0) or 0
            end_val = end_data.get(printer, {}).get(field, 0) or 0

            diff[printer][field] = end_val - start_val

        # 🔥 أضيف هذه القيم حتى لا يحدث KeyError في الـ PDF
        diff[printer]["used"] = diff[printer].get("Total", 0)
        diff[printer]["jam"] = diff[printer].get("Jam", 0)
        diff[printer]["1s"] = diff[printer].get("One Side", 0)
        diff[printer]["2s"] = diff[printer].get("Two Side", 0)

    return diff


# =====================================================
# PRINTER MANAGEMENT UI (ADD / EDIT / DELETE)
# =====================================================

def printer_management_ui(db):

    st.title("🖨 Printer Management")

    if "printers" not in db:
        db["printers"] = {}

    printers = db["printers"].copy()

    st.subheader("📋 Current Printers")

    if not printers:
        st.info("No printers added yet.")

    for name, ip in printers.items():

        with st.expander(f"📠 {name}"):

            new_name = st.text_input(
                "Printer Name",
                value=name,
                key=f"name_{name}"
            )

            new_ip = st.text_input(
                "Printer IP",
                value=ip,
                key=f"ip_{name}"
            )

            col1, col2 = st.columns(2)

            # ---------------- SAVE ----------------
            with col1:
                if st.button("💾 Save Changes", key=f"save_{name}"):

                    if not new_name.strip():
                        st.warning("Printer name cannot be empty.")
                        return

                    if new_name != name and new_name in db["printers"]:
                        st.error("Printer name already exists.")
                        return

                    # remove old if renamed
                    if new_name != name:
                        del db["printers"][name]

                    db["printers"][new_name] = new_ip.strip()

                    save_db(db)
                    st.success("Updated Successfully ✅")
                    st.rerun()

            # ---------------- DELETE ----------------
            with col2:
                if st.button("❌ Delete Printer", key=f"delete_{name}"):

                    del db["printers"][name]
                    save_db(db)

                    st.warning("Printer Deleted")
                    st.rerun()

    st.divider()

    # =====================================================
    # ADD NEW PRINTER
    # =====================================================

    st.subheader("➕ Add New Printer")

    add_name = st.text_input("New Printer Name")
    add_ip = st.text_input("New Printer IP")

    if st.button("Add Printer", use_container_width=True):

        if not add_name.strip():
            st.warning("Enter printer name.")
            return

        if add_name in db["printers"]:
            st.error("Printer already exists.")
            return

        db["printers"][add_name.strip()] = add_ip.strip()

        save_db(db)
        st.success("Printer Added ✅")
        st.rerun()


# =====================================================
# SHIFT INPUT TAB
# =====================================================

def printer_shift_tab(title, key_prefix):

    st.markdown(f"## {title}")

    printer_data = {}
    printers = get_printers()

    if not printers:
        st.info("No printers configured.")
        return printer_data

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
# SHIFT COMPARISON PAGE
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

        if not diff:
            st.info("No data to compare.")
            return

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
