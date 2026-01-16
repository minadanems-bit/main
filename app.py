import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
import io
import base64
import urllib.parse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. Database Configuration ---
DB_FILE = 'nms_enterprise_pro_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    # Initial structure if file doesn't exist at all
    initial_default = {
        "logo": None,
        "branches": ["M. Nageb Branch", "Tram Branch"],
        "expense_categories": ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Rent", "Other"],
        "users": {
            "admin": {
                "pass": "admin123", "role": "admin", "full_name": "Manager",
                "phone": "", "national_id": "", "address": "", "email": "",
                "social_status": "Single", "qualification": "", "hiring_date": "2024-01-01",
                "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": []
            }
        },
        "tasks": {
            "opening": ["Fingerprint Attendance", "Power On Devices", "Uniform & Name Tag", "Music & Ambience", "Paper Loaded", "Cash Counted", "Clean Windows & Counters", "Check Internet Connection", "Check Supplies Inventory"],
            "closing": ["Save WhatsApp Contacts", "Cleaning Workplace", "Power Off Devices", "Trash Removed", "Fingerprint Sign-out", "Daily Report Sent", "Safe Locked", "Lights Off"],
            "social": ["Canva Design 1", "Canva Design 2", "WhatsApp Story", "WhatsApp Channel", "Facebook Account Story", "Facebook Account Post/Reel", "Facebook Account Group", "Facebook Page Story", "Facebook Page Post/Reel", "Threads Post", "Instagram Story", "Instagram Post/Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
            "interaction": ["Like", "Love", "Care", "Share", "Comment", "Reply to Messages", "Join Groups"]
        },
        "history": [], "drafts": {}, "logs": []
    }

    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return initial_default

    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Critical Fix: Ensure existing users are not overwritten by the script's defaults
            if "users" not in data or not data["users"]:
                data["users"] = initial_default["users"]
            
            # Fill missing keys for each user to prevent crashes without losing data
            for user_id in data["users"]:
                u = data["users"][user_id]
                default_keys = {
                    "pass": "123", "role": "user", "full_name": user_id,
                    "phone": "", "national_id": "", "address": "", "email": "",
                    "social_status": "Single", "qualification": "", "hiring_date": "2024-01-01",
                    "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": []
                }
                for key, val in default_keys.items():
                    if key not in u:
                        u[key] = val
            
            # Sync tasks categories if they changed in the code but keep old ones if needed
            for cat in initial_default["tasks"]:
                if cat not in data.get("tasks", {}):
                    if "tasks" not in data: data["tasks"] = {}
                    data["tasks"][cat] = initial_default["tasks"][cat]
            
            return data
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return initial_default

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

# --- 2. Session Setup ---
st.set_page_config(page_title="NMS ERP Ultimate", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        draft_keys = ('s_','o_','e_','c_','m_','i_','ks','xs','op','u10','v22','ex','kj','xj','dn','k1','k2','x1','x2')
        draft_data = {k: v for k, v in st.session_state.items() if k.startswith(draft_keys)}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = draft_data
        save_db(db)

# --- 3. Login Section ---
if not st.session_state['logged_in']:
    st.title("🔐 NMS Enterprise Management")
    c1, c2 = st.columns(2)
    with c1:
        if db.get("logo"): 
            try: st.image(base64.b64decode(db["logo"]), width=300)
            except: st.info("Logo format error")
        else: st.info("No Logo Set")
    with c2:
        # Show all users from the JSON file
        u_list = list(db["users"].keys())
        u_name = st.selectbox("Select Your Account", u_list)
        u_pass = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if db["users"][u_name]["pass"] == u_pass:
                st.session_state.update({'logged_in': True, 'user': u_name, 'role': db["users"][u_name]["role"]})
                if u_name in db.get("drafts", {}):
                    for key, val in db["drafts"][u_name].items(): st.session_state[key] = val
                db["logs"].append({"user": u_name, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Invalid Password")

else:
    # --- 4. Sidebar ---
    with st.sidebar:
        st.header(f"User: {db['users'][st.session_state['user']]['full_name']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            admin_choice = st.selectbox("Admin Menu", ["HR & Profiles", "Payroll", "Tasks", "Branches", "History"])

            if admin_choice == "HR & Profiles":
                st.write("### Employee Directory")
                target = st.selectbox("Edit Employee", list(db["users"].keys()))
                u_profile = db["users"][target]
                with st.expander("Personal Details", expanded=True):
                    up_full = st.text_input("Full Name", value=u_profile.get('full_name', ''))
                    up_pass = st.text_input("Password", value=u_profile.get('pass', ''))
                    up_phone = st.text_input("Phone", value=u_profile.get('phone', ''))
                    up_nid = st.text_input("National ID", value=u_profile.get('national_id', ''))
                    up_addr = st.text_area("Address", value=u_profile.get('address', ''))
                    up_mail = st.text_input("Email", value=u_profile.get('email', ''))
                    up_stat = st.selectbox("Status", ["Single", "Married", "Other"], index=0)
                    up_qual = st.text_input("Qualification", value=u_profile.get('qualification', ''))
                    if st.button("Update Profile"):
                        db["users"][target].update({"full_name": up_full, "pass": up_pass, "phone": up_phone, "national_id": up_nid, "address": up_addr, "email": up_mail, "social_status": up_stat, "qualification": up_qual})
                        save_db(db); st.success("Updated")
                
                st.divider()
                st.write("#### Add New Staff")
                new_un = st.text_input("New Username")
                if st.button("Create"):
                    if new_un and new_un not in db["users"]:
                        db["users"][new_un] = {"pass": "123", "role": "user", "full_name": new_un, "phone": "", "national_id": "", "address": "", "email": "", "social_status": "Single", "qualification": "", "hiring_date": str(date.today()), "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": []}
                        save_db(db); st.success("Account Created"); st.rerun()

            elif admin_choice == "Payroll":
                target = st.selectbox("Select Staff Member", list(db["users"].keys()))
                u_fin = db["users"][target]
                sal = st.number_input("Base Salary", value=float(u_fin.get('salary', 0)))
                hire = st.date_input("Hiring Date", value=datetime.strptime(u_fin.get('hiring_date', "2024-01-01"), "%Y-%m-%d"))
                if st.button("Save HR Contract"):
                    db["users"][target]["salary"] = sal
                    db["users"][target]["hiring_date"] = str(hire)
                    save_db(db); st.success("Contract Saved")
                st.divider()
                dev_cat = st.radio("Entry Type", ["Bonus", "Deduction", "Overtime", "Extra Leave"], horizontal=True)
                amt = st.number_input("Value", step=10.0)
                note = st.text_area("Note")
                if st.button("Add Financial Entry"):
                    key = dev_cat.lower().replace(" ", "_")
                    db["users"][target][key].append({"date": str(date.today()), "val": amt, "note": note})
                    save_db(db); st.success("Entry Recorded")

            elif admin_choice == "Tasks":
                t_cat = st.selectbox("Edit Category", ["opening", "closing", "social", "interaction"])
                for i, t in enumerate(db["tasks"][t_cat]):
                    ct1, ct2 = st.columns([5, 1])
                    ct1.text(f"• {t}")
                    if ct2.button("X", key=f"t_del_{t_cat}_{i}"):
                        db["tasks"][t_cat].pop(i); save_db(db); st.rerun()
                nt = st.text_input("New Task Text")
                if st.button("Add Task Item"):
                    if nt: db["tasks"][t_cat].append(nt); save_db(db); st.rerun()

            elif admin_choice == "Branches":
                st.write("### Branch Locations")
                for i, b in enumerate(db["branches"]): st.text(f"- {b}")
                st.divider()
                st.write("### Expenses List")
                for i, e in enumerate(db["expense_categories"]):
                    ce1, ce2 = st.columns([5,1]); ce1.text(e)
                    if ce2.button("X", key=f"ex_del_{i}"):
                        db["expense_categories"].pop(i); save_db(db); st.rerun()
                new_ex = st.text_input("New Expense Cat")
                if st.button("Add Expense"):
                    if new_ex: db["expense_categories"].append(new_ex); save_db(db); st.rerun()

            elif admin_choice == "History":
                if db["history"]: st.dataframe(pd.DataFrame(db["history"]))
                if st.button("Delete History", type="primary"): db["history"] = []; save_db(db); st.rerun()

    # --- 5. Main Content ---
    st.title("📊 NMS ERP Dashboard")
    m1, m2, m3, m4 = st.columns(4)
    with m1: branch = st.selectbox("Branch", db["branches"])
    with m2: shift = st.selectbox("Shift", ["Morning", "Night"])
    with m3: st.info(f"Date: {date.today()}")
    with m4: st.info(f"User: {st.session_state['user']}")

    tab1, tab2, tab3 = st.tabs(["OPENING", "CLOSING", "SOCIAL"])

    with tab1:
        c_o1, c_o2, c_o3 = st.columns([1, 1.5, 1.5])
        with c_o1:
            st.write("#### Checklists")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c_o2:
            st.write("#### Opening Cash")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, key="o_coins", on_change=sync_draft)
            t_open += o_coins
            st.success(f"Total: {t_open:,.2f}")
        with c_o3:
            st.write("#### Counters")
            ks = st.number_input("Kyo Start", step=1, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Start", step=0.01, key="ops", on_change=sync_draft)
            u10 = st.number_input("U10 (Debit In)", step=1.0, key="u10_val", on_change=sync_draft)

    with tab2:
        c_c1, c_c2, c_c3 = st.columns([1, 1.5, 1.5])
        with c_c1:
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales", on_change=sync_draft)
            insta = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wall = st.number_input("Wallet", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1.0, key="c_visa", on_change=sync_draft)
            v22 = st.number_input("V22 (Debit Out)", step=1.0, key="v22_val", on_change=sync_draft)
        with c_c2:
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Coins ", step=0.5, key="c_coins", on_change=sync_draft)
            t_close += c_coins
            st.divider()
            ex_cat = st.selectbox("Exp Category", db["expense_categories"], key="ex_cat")
            ex_val = st.number_input("Exp Amount", step=1.0, key="ex_val")
            ex_note = st.text_input("Exp Reason", key="ex_note")
            expected = t_open + sys_sales + u10 - ex_val - v22 - (insta + wall + visa)
            diff = t_close - expected
            st.metric("Expected", f"{expected:,.2f}")
            st.metric("Diff", f"{diff:,.2f}")
        with c_c3:
            st.write("**Kyocera**")
            ke = st.number_input("Kyo End", step=1, key="ke")
            k1s = st.number_input("Kyo 1-Side", step=1, key="k1s_v")
            k2s = st.number_input("Kyo 2-Sides", step=1, key="k2s_v")
            kj = st.number_input("Kyo Paper Jam", step=1, key="kj_v", on_change=sync_draft)
            st.write("**Xerox**")
            xe = st.number_input("Xerox End", step=1, key="xe")
            x1s = st.number_input("Xerox 1-Side", step=1, key="x1s_v")
            x2s = st.number_input("Xerox 2-Sides", step=1, key="x2s_v")
            xj = st.number_input("Xerox Paper Jam", step=1, key="xj_v", on_change=sync_draft)
            st.divider()
            ope = st.number_input("Opay End", step=0.01, key="ope")
            st.text_area("Notes", key="dn_notes", on_change=sync_draft)

    with tab3:
        sc1, sc2 = st.columns(2)
        with sc1:
            for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        with sc2:
            for t in db["tasks"]["interaction"]: st.checkbox(t, key=f"i_{t}", on_change=sync_draft)
        st.divider()
        wa_text = f"NMS REPORT\nBranch: {branch}\nSales: {sys_sales}\nExp: {ex_val}\nDiff: {diff}\nKyo: {ke-ks}\nXerox: {xe-xs}"
        if st.button("FINISH SHIFT", use_container_width=True):
            db["history"].append({"date": str(date.today()), "branch": branch, "staff": st.session_state['user'], "sales": sys_sales, "diff": diff})
            if st.session_state['user'] in db["drafts"]: del db["drafts"][st.session_state['user']]
            save_db(db); st.success("Shift Archived")
        c_p, c_w = st.columns(2)
        with c_p:
            if st.button("PDF", use_container_width=True):
                buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
                styles = getSampleStyleSheet(); parts = [Paragraph(f"NMS Report {date.today()}", styles['Title'])]
                p_data = [["Item", "Value"], ["Sales", sys_sales], ["Diff", diff]]
                tbl = Table(p_data, colWidths=[200, 200]); tbl.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
                parts.append(tbl); doc.build(parts)
                st.download_button("Download PDF", buf.getvalue(), "Report.pdf")
        with c_w:
            url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; font-weight:bold;">WHATSAPP</button></a>', unsafe_allow_html=True)
