import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
import io
import base64
import urllib.parse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. Database Engine ---
DB_FILE = 'nms_enterprise_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "salary": 0.0, "hiring_date": "2024-01-01", "bonus": [], "deductions": []},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "salary": 3000.0, "hiring_date": "2024-01-01", "bonus": [], "deductions": []}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "expense_categories": ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Other"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [],
            "drafts": {},
            "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        # Structural Sanity Checks
        if "history" not in data: data["history"] = []
        if "expense_categories" not in data: data["expense_categories"] = ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Other"]
        if "tasks" not in data: data["tasks"] = {"opening":[], "closing":[], "social":[], "interaction":[]}
        for user in data["users"]:
            if "bonus" not in data["users"][user]: data["users"][user]["bonus"] = []
            if "deductions" not in data["users"][user]: data["users"][user]["deductions"] = []
            if "salary" not in data["users"][user]: data["users"][user]["salary"] = 0.0
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & Session Logic ---
st.set_page_config(page_title="NMS ERP - Comprehensive Control", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_', 'exp_'))}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# --- 3. Login System ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Enterprise Login")
    col1, col2 = st.columns([1, 1])
    with col1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=250)
        else: st.info("NMS ERP System")
    with col2:
        u = st.selectbox("Select Employee", list(db["users"].keys()))
        p = st.text_input("Password", type="password")
        if st.button("Login to System", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items():
                        st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Authentication Failed")

else:
    # --- 4. Sidebar & Admin Panel ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"Welcome, {db['users'][st.session_state['user']]['full_name']}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Master Control")
            admin_mode = st.radio("Management Suite", [
                "HR & Payroll", 
                "Manage Tasks", 
                "Financial History", 
                "System Settings", 
                "Audit Logs"
            ])
            
            # --- ADMIN: HR & PAYROLL ---
            if admin_mode == "HR & Payroll":
                st.subheader("👥 HR & Payroll")
                target_emp = st.selectbox("Employee", list(db["users"].keys()))
                emp_data = db["users"][target_emp]
                
                hr_tab1, hr_tab2 = st.tabs(["Salary & Contract", "Bonus/Deduction"])
                with hr_tab1:
                    new_base = st.number_input("Base Salary", value=float(emp_data.get('salary', 0)))
                    if st.button("Save Salary"):
                        db["users"][target_emp]["salary"] = new_base
                        save_db(db); st.success("Saved")
                    
                    # Manage Employee Account
                    st.divider()
                    st.write("Edit Credentials")
                    new_pass = st.text_input("Change Password", value=emp_data['pass'])
                    if st.button("Update Account"):
                        db["users"][target_emp]["pass"] = new_pass
                        save_db(db); st.success("Account Updated")
                    if target_emp != "admin" and st.button("🗑️ Delete Employee", type="primary"):
                        del db["users"][target_emp]
                        save_db(db); st.rerun()

                with hr_tab2:
                    st.write("Grant Reward/Penalty")
                    amt = st.number_input("Amount", step=10.0)
                    reason = st.text_input("Reason")
                    col_b, col_d = st.columns(2)
                    if col_b.button("➕ Bonus"):
                        db["users"][target_emp]["bonus"].append({"date": str(date.today()), "amt": amt, "reason": reason})
                        save_db(db); st.success("Bonus Added")
                    if col_d.button("➖ Deduction"):
                        db["users"][target_emp]["deductions"].append({"date": str(date.today()), "amt": amt, "reason": reason})
                        save_db(db); st.warning("Deduction Added")

            # --- ADMIN: MANAGE TASKS (The missing feature) ---
            elif admin_mode == "Manage Tasks":
                st.subheader("📋 Task Lists Management")
                task_cat = st.selectbox("Select Task Category", ["opening", "closing", "social", "interaction"])
                
                # List current tasks
                st.write(f"Current {task_cat.capitalize()} Tasks:")
                for i, t in enumerate(db["tasks"][task_cat]):
                    c1, c2 = st.columns([4, 1])
                    c1.text(f"- {t}")
                    if c2.button("🗑️", key=f"del_{task_cat}_{i}"):
                        db["tasks"][task_cat].pop(i)
                        save_db(db); st.rerun()
                
                st.divider()
                new_task = st.text_input("Add New Task")
                if st.button("➕ Add to List"):
                    if new_task:
                        db["tasks"][task_cat].append(new_task)
                        save_db(db); st.success("Task Added"); st.rerun()

            # --- ADMIN: SYSTEM SETTINGS ---
            elif admin_mode == "System Settings":
                st.subheader("⚙️ System Configuration")
                # Manage Branches
                st.write("### Branches")
                for i, b in enumerate(db["branches"]):
                    col_b1, col_b2 = st.columns([4, 1])
                    col_b1.text(b)
                    if col_b2.button("🗑️", key=f"del_br_{i}"):
                        db["branches"].pop(i)
                        save_db(db); st.rerun()
                new_branch = st.text_input("Add Branch Name")
                if st.button("Add Branch"):
                    db["branches"].append(new_branch); save_db(db); st.rerun()
                
                st.divider()
                # Manage Expense Categories
                st.write("### Expense Categories")
                for i, ex in enumerate(db["expense_categories"]):
                    col_e1, col_e2 = st.columns([4, 1])
                    col_e1.text(ex)
                    if col_e2.button("🗑️", key=f"del_ex_{i}"):
                        db["expense_categories"].pop(i)
                        save_db(db); st.rerun()
                new_ex = st.text_input("Add Category")
                if st.button("Add Category"):
                    db["expense_categories"].append(new_ex); save_db(db); st.rerun()

            elif admin_mode == "Financial History":
                st.subheader("📜 History Explorer")
                if db["history"]:
                    st.dataframe(pd.DataFrame(db["history"]))
                    if st.button("Clear All History (Danger)", type="primary"):
                        db["history"] = []; save_db(db); st.rerun()

    # --- 5. Main Dashboard (User Interface) ---
    st.title("📊 Shift Operations")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    with inf2: branch = st.selectbox("Branch", db["branches"])
    with inf3: shift = st.selectbox("Shift", ["Morning", "Night"])
    with inf4: st.info(f"👤 {st.session_state['user']}")

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])

    with tab1:
        st.subheader("Opening")
        c1, c2 = st.columns(2)
        with c1:
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            k_start = st.number_input("Kyocera Start", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            u10_debit = st.number_input("Debit Received", step=1.0, key="u10_val", on_change=sync_draft)

    with tab2:
        st.subheader("Closing")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales", on_change=sync_draft)
            t_close = st.number_input("Actual Cash in Drawer", step=1.0, key="cc_total", on_change=sync_draft)
            v22_debit = st.number_input("Debit Postponed", step=1.0, key="v22_val", on_change=sync_draft)
        with col_c2:
            exp_cat = st.selectbox("Exp Category", db["expense_categories"], key="exp_cat_sel")
            exp_val = st.number_input("Exp Amount", step=1.0, key="c_exp")
            exp_note = st.text_input("Exp Note")
            
            # Auto-calculation (Simplified for demo)
            expected = sys_sales + u10_debit - exp_val - v22_debit
            st.metric("Expected", f"{expected:,.2f}")
            net_diff = t_close - expected
            st.metric("Difference", f"{net_diff:,.2f}")

    with tab3:
        st.subheader("Social Media & Interaction")
        sc1, sc2 = st.columns(2)
        with sc1:
            for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        with sc2:
            for t in db["tasks"]["interaction"]: st.checkbox(t, key=f"i_{t}", on_change=sync_draft)

    # --- 6. Archive ---
    st.divider()
    if st.button("🏁 ARCHIVE SHIFT", use_container_width=True):
        entry = {
            "date": str(date.today()),
            "staff": st.session_state['user'],
            "branch": branch,
            "sales": sys_sales,
            "expenses": exp_val,
            "diff": net_diff
        }
        db["history"].append(entry)
        save_db(db); st.success("Shift Saved to History")
