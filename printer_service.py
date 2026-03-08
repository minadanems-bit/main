# printer_service.py
import streamlit as st
from database_service import load_db, save_db

def init_printers():
    db = load_db()
    if "printers" not in db:
        db["printers"] = {
            "Kyocera 3010i": "192.168.1.120",
            "Xerox 7835": "192.168.1.65",
            "Kyocera P5031DN": "192.168.1.126",
            "Print N' Go": "192.168.1.130"
        }
        save_db(db)

init_printers()

def get_printers():
    db = load_db()
    return db.get("printers", {})

def calculate_printer_difference(start_data, end_data):
    diff = {}
    # union of printer names present in start/end
    printers = set(start_data.keys()) | set(end_data.keys())
    fields = ["Total", "One Side", "Two Side", "Errors", "Jam"]
    for p in printers:
        diff[p] = {}
        for f in fields:
            s = start_data.get(p, {}).get(f, 0) or 0
            e = end_data.get(p, {}).get(f, 0) or 0
            try:
                diff[p][f] = int(e) - int(s)
            except:
                # fallback if non-int
                try:
                    diff[p][f] = float(e) - float(s)
                except:
                    diff[p][f] = 0
        # replicate friendly keys for PDF/WA
        diff[p]["used"] = diff[p].get("Total", 0)
        diff[p]["jam"] = diff[p].get("Jam", 0)
        diff[p]["1s"] = diff[p].get("One Side", 0)
        diff[p]["2s"] = diff[p].get("Two Side", 0)
    return diff

# Optional: simple UI used by admin (can be imported into a page)
def printer_management_ui():
    db = load_db()
    if "printers" not in db:
        db["printers"] = {}
    st.title("🖨 Printer Management")
    printers = db["printers"].copy()
    for name, ip in printers.items():
        with st.expander(name):
            new_name = st.text_input("Name", value=name, key=f"name_{name}")
            new_ip = st.text_input("IP", value=ip, key=f"ip_{name}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Save", key=f"save_{name}"):
                    if new_name != name and new_name in db["printers"]:
                        st.error("Name exists")
                    else:
                        if new_name != name:
                            del db["printers"][name]
                        db["printers"][new_name] = new_ip
                        save_db(db); st.success("Saved"); st.rerun()
            with c2:
                if st.button("Delete", key=f"del_{name}"):
                    del db["printers"][name]; save_db(db); st.success("Deleted"); st.rerun()
    st.divider()
    st.subheader("➕ Add Printer")
    add_name = st.text_input("New printer name")
    add_ip = st.text_input("New printer ip")
    if st.button("Add Printer"):
        if add_name:
            db["printers"][add_name] = add_ip
            save_db(db)
            st.success("Added")
            st.rerun()
