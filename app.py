import streamlit as st
import pandas as pd
from datetime import datetime
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
            "logo": None, "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار", "كهرباء ومياه"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["WhatsApp Story", "Facebook Post", "Instagram Reel", "TikTok Story", "Threads", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [], "drafts": {}, "history": [], "payroll_history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        for u in data["users"]:
            for key in ["salary", "advances", "deductions", "bonus", "off_days"]:
                if key not in data["users"][u]: data["users"][u][key] = 0
        if "payroll_history" not in data: data["payroll_history"] = []
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & Session ---
st.set_page_config(page_title="NMS ERP", layout="wide")
if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'user': None, 'role': None})
if 'exp_list' not in st.session_state: st.session_state.exp_list = []

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_'))}
        current_data['exp_list'] = st.session_state.exp_list
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# --- 3. Login ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Enterprise Login")
    u = st.selectbox("Employee", list(db["users"].keys()))
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if db["users"][u]["pass"] == p:
            st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
            if u in db.get("drafts", {}):
                for k, v in db["drafts"][u].items():
                    if k == 'exp_list': st.session_state.exp_list = v
                    else: st.session_state[k] = v
            st.rerun()
else:
    # --- 4. Sidebar ---
    with st.sidebar:
        st.header(f"Welcome, {st.session_state['user']}")
        u_node = db["users"][st.session_state['user']]
        if st.session_state['role'] != 'admin':
            st.info(f"💰 My Wallet:\n- Bal: {u_node['salary']}\n- Adv: {u_node['advances']}\n- Net: {u_node['salary'] + u_node['bonus'] - u_node['advances'] - u_node['deductions']}")
        
        if st.button("Logout"): st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            mode = st.radio("Management", ["Payroll Center", "Employees", "Branches", "Tasks & Expenses", "History"])

            if mode == "Payroll Center":
                st.subheader("💳 Payroll Management")
                emp = st.selectbox("Select Employee", [u for u in db["users"].keys() if u != 'admin'])
                u_d = db["users"][emp]
                c1, c2 = st.columns(2)
                with c1:
                    db["users"][emp]["salary"] = st.number_input("Basic Salary", value=float(u_d['salary']))
                    adv = st.number_input("Add Advance", 0.0)
                    ded = st.number_input("Add Deduction", 0.0)
                with c2:
                    bon = st.number_input("Add Bonus", 0.0)
                    off = st.number_input("Add Off Days", 0)
                    if st.button("Save Financials"):
                        db["users"][emp]["advances"] += adv
                        db["users"][emp]["deductions"] += ded
                        db["users"][emp]["bonus"] += bon
                        db["users"][emp]["off_days"] += off
                        save_db(db); st.success("Updated!"); st.rerun()
                
                net = u_d['salary'] + u_d['bonus'] - u_d['advances'] - u_d['deductions']
                st.metric("Net Salary", f"{net} LE")
                
                # --- PDF Salary Slip Generator ---
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = [Paragraph(f"Salary Slip: {emp} - {datetime.now().strftime('%B %Y')}", getSampleStyleSheet()['Title'])]
                data = [["Description", "Amount"], ["Basic Salary", u_d['salary']], ["Bonus", u_d['bonus']], ["Advances", u_d['advances']], ["Deductions", u_d['deductions']], ["Total Net", net]]
                t = Table(data, colWidths=[200, 100])
                t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke)]))
                elements.append(t)
                doc.build(elements)
                st.download_button(f"📥 Download PDF for {emp}", buffer.getvalue(), f"Slip_{emp}.pdf")
                
                if st.button("🔴 RESET & CLOSE MONTH"):
                    db["users"][emp].update({"advances": 0, "deductions": 0, "bonus": 0, "off_days": 0})
                    save_db(db); st.success("Month Reset!"); st.rerun()

            elif mode == "Employees":
                st.subheader("Manage Employees")
                with st.expander("Add New"):
                    nu = st.text_input("Username")
                    np = st.text_input("Pass")
                    if st.button("Create"):
                        db["users"][nu] = {"pass": np, "role": "user", "full_name": nu, "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0}
                        save_db(db); st.rerun()
                target = st.selectbox("Select to Delete", list(db["users"].keys()))
                if st.button("Delete Employee") and target != 'admin':
                    del db["users"][target]; save_db(db); st.rerun()

            elif mode == "Branches":
                st.subheader("Manage Branches")
                nb = st.text_input("New Branch")
                if st.button("Add Branch"): db["branches"].append(nb); save_db(db); st.rerun()
                db["branches"] = st.multiselect("Active Branches", db["branches"], default=db["branches"])
                if st.button("Update Branches"): save_db(db); st.rerun()

            elif mode == "Tasks & Expenses":
                cat = st.selectbox("Task Category", ["Opening", "Closing", "Social"])
                new_t = st.text_input("New Task")
                if st.button("Add Task"): db["tasks"][cat.lower()].append(new_t); save_db(db); st.rerun()
                st.divider()
                new_ex = st.text_input("New Expense Category")
                if st.button("Add Expense Cat"): db["exp_categories"].append(new_ex); save_db(db); st.rerun()

    # --- 5. Main Dashboard ---
    st.title("📊 Daily Shift Control")
    branch = st.selectbox("Branch", db["branches"])
    shift = st.selectbox("Shift", ["Morning", "Night"])
    
    t1, t2, t3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])
    
    with t1:
        st.subheader("Opening")
        for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        t_open = 0.0
        for d in [200, 100, 50, 20, 10, 5]:
            t_open += st.number_input(f"{d} LE", 0, key=f"o_{d}", on_change=sync_draft) * d
        ks = st.number_input("Kyo Start", key="ks", on_change=sync_draft)
        xs = st.number_input("Xerox Start", key="xs", on_change=sync_draft)

    with t2:
        st.subheader("Closing")
        sys_sales = st.number_input("System Sales", key="c_sys_sales", on_change=sync_draft)
        e_type = st.selectbox("Exp Category", db["exp_categories"])
        e_amt = st.number_input("Exp Amount", key="e_amt")
        if st.button("Add Expense"):
            st.session_state.exp_list.append({"Type": e_type, "Amount": e_amt})
            sync_draft(); st.rerun()
        
        exp_total = sum(item['Amount'] for item in st.session_state.exp_list)
        st.write(f"Total Expenses: {exp_total}")
        
        t_close = 0.0
        for d in [200, 100, 50, 20, 10, 5]:
            t_close += st.number_input(f"{d} LE ", 0, key=f"c_{d}", on_change=sync_draft) * d
        
        expected = t_open + sys_sales - exp_total
        diff = t_close - expected
        st.metric("Expected", expected, delta=diff)
        
        st.markdown("### 🖨️ Printer Check")
        ke = st.number_input("Kyo End", key="k1end")
        xe = st.number_input("Xerox End", key="x2end")
        st.write(f"Kyo Used: {ke-ks} | Xerox Used: {xe-xs}")

    with t3:
        for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)

    # --- 6. Archive & Export ---
    if st.button("🏁 FINALIZE SHIFT"):
        archive = {"date": str(datetime.now().date()), "staff": st.session_state['user'], "branch": branch, "sales": sys_sales, "diff": diff}
        db["history"].append(archive); save_db(db)
        st.success("Archived!"); st.rerun()

    wa_msg = f"NMS Report: {branch}\nSales: {sys_sales}\nDiff: {diff}"
    wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px;">📱 SEND WHATSAPP</button></a>', unsafe_allow_html=True)
