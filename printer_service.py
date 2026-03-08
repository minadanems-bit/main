# =====================================================
# PRINTER SERVICE (REFACTORED VERSION)
# =====================================================

import streamlit as st

from database import load_db, save_db


# =====================================================
# Constants
# =====================================================
DEFAULT_PRINTERS = {
    "Kyocera 3010i": "192.168.1.120",
    "Xerox 7835": "192.168.1.65",
    "Kyocera P5031DN": "192.168.1.126",
}

PRINTER_FIELDS = ["Total", "One Side", "Two Side", "Errors", "Jam"]


# =====================================================
# Helpers
# =====================================================
def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _normalize_printer_counter_data(data: dict) -> dict:
    normalized = {}

    for printer_name, values in (data or {}).items():
        normalized[printer_name] = {
            "Total": _safe_int(values.get("Total", 0)),
            "One Side": _safe_int(values.get("One Side", 0)),
            "Two Side": _safe_int(values.get("Two Side", 0)),
            "Errors": _safe_int(values.get("Errors", 0)),
            "Jam": _safe_int(values.get("Jam", 0)),
        }

    return normalized


def _ensure_printers_in_db(db: dict) -> bool:
    changed = False

    if "printers" not in db or not isinstance(db["printers"], dict):
        db["printers"] = DEFAULT_PRINTERS.copy()
        changed = True

    return changed


# =====================================================
# Initialization
# =====================================================
def init_printers() -> None:
    db = load_db()
    changed = _ensure_printers_in_db(db)

    if changed:
        save_db(db)


init_printers()


# =====================================================
# Public API
# =====================================================
def get_printers() -> dict:
    db = load_db()
    _ensure_printers_in_db(db)
    return db.get("printers", {})


def calculate_printer_difference(start_data: dict, end_data: dict) -> dict:
    start_data = _normalize_printer_counter_data(start_data)
    end_data = _normalize_printer_counter_data(end_data)

    diff = {}
    all_printers = set(start_data.keys()) | set(end_data.keys())

    for printer in all_printers:
        diff[printer] = {}

        for field in PRINTER_FIELDS:
            start_val = start_data.get(printer, {}).get(field, 0)
            end_val = end_data.get(printer, {}).get(field, 0)
            diff[printer][field] = end_val - start_val

        # Compatibility keys used by PDF/report modules
        diff[printer]["used"] = diff[printer].get("Total", 0)
        diff[printer]["jam"] = diff[printer].get("Jam", 0)
        diff[printer]["1s"] = diff[printer].get("One Side", 0)
        diff[printer]["2s"] = diff[printer].get("Two Side", 0)

    return diff


# =====================================================
# Printer Management UI
# =====================================================
def printer_management_ui(db: dict) -> None:
    st.title("🖨 Printer Management")

    if _ensure_printers_in_db(db):
        save_db(db)

    st.subheader("📋 Current Printers")
    printers = db.get("printers", {})

    if not printers:
        st.info("No printers added yet.")

    for original_name, original_ip in list(printers.items()):
        with st.expander(f"📠 {original_name}"):
            new_name = st.text_input(
                "Printer Name",
                value=original_name,
                key=f"name_{original_name}",
            )

            new_ip = st.text_input(
                "Printer IP",
                value=original_ip,
                key=f"ip_{original_name}",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Save Changes", key=f"save_{original_name}"):
                    cleaned_name = new_name.strip()
                    cleaned_ip = new_ip.strip()

                    if not cleaned_name:
                        st.warning("Printer name cannot be empty.")
                        st.stop()

                    if cleaned_name != original_name and cleaned_name in db["printers"]:
                        st.error("Printer name already exists.")
                        st.stop()

                    if cleaned_name != original_name:
                        del db["printers"][original_name]

                    db["printers"][cleaned_name] = cleaned_ip
                    save_db(db)
                    st.success("Updated Successfully ✅")
                    st.rerun()

            with col2:
                if st.button("❌ Delete Printer", key=f"delete_{original_name}"):
                    del db["printers"][original_name]
                    save_db(db)
                    st.warning("Printer Deleted")
                    st.rerun()

    st.divider()
    st.subheader("➕ Add New Printer")

    add_name = st.text_input("New Printer Name")
    add_ip = st.text_input("New Printer IP")

    if st.button("Add Printer", use_container_width=True):
        cleaned_name = add_name.strip()
        cleaned_ip = add_ip.strip()

        if not cleaned_name:
            st.warning("Enter printer name.")
            st.stop()

        if cleaned_name in db["printers"]:
            st.error("Printer already exists.")
            st.stop()

        db["printers"][cleaned_name] = cleaned_ip
        save_db(db)
        st.success("Printer Added ✅")
        st.rerun()


# =====================================================
# Shift Inputs
# =====================================================
def printer_shift_tab(title: str, key_prefix: str) -> dict:
    st.markdown(f"## {title}")

    printer_data = {}
    printers = get_printers()

    if not printers:
        st.info("No printers configured.")
        return printer_data

    for printer_name in printers.keys():
        st.markdown(f"### 📠 {printer_name}")

        base_key = f"{key_prefix}_{printer_name}"

        total = st.number_input("✔ Total", min_value=0, step=1, key=f"{base_key}_total")
        one_side = st.number_input("✔ 1 Side", min_value=0, step=1, key=f"{base_key}_one")
        two_side = st.number_input("✔ 2 Side", min_value=0, step=1, key=f"{base_key}_two")
        errors = st.number_input("❌ Errors", min_value=0, step=1, key=f"{base_key}_errors")
        jam = st.number_input("⚠ Jam", min_value=0, step=1, key=f"{base_key}_jam")

        printer_data[printer_name] = {
            "Total": total,
            "One Side": one_side,
            "Two Side": two_side,
            "Errors": errors,
            "Jam": jam,
        }

        st.divider()

    return printer_data


# =====================================================
# Shift Comparison
# =====================================================
def printer_shift_comparison() -> None:
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

        for printer_name, values in diff.items():
            st.markdown(f"### 📠 {printer_name}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total", values.get("Total", 0))
            col2.metric("1 Side", values.get("One Side", 0))
            col3.metric("2 Side", values.get("Two Side", 0))

            col4, col5 = st.columns(2)
            col4.metric("Errors", values.get("Errors", 0))
            col5.metric("Jam", values.get("Jam", 0))

            st.divider()
