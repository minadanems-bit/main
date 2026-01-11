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

# --- 1. Database Configuration ---
DB_FILE = 'nms_enterprise_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0, "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0, "photo": None}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار", "كهرباء ومياه"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [], "drafts": {}, "history": [], "payroll_history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        if "history" not in data: data["history"] = []
        if "payroll_history" not in data: data["payroll_history"] = []
        for u in data["users"]:
            for key in ["salary", "advances", "deductions", "bonus", "off_days"]:
                if key not in data["users"][u]: data["users"][u][key] = 0
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Session Logic ---
st.set_page_config(page_title="NMS ERP System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})
if 'exp_list' not in st.session_state:
    st.session_state.exp_list = []

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_'))}
        current_data['exp_list'] = st.session_state.exp_list
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# --- 3. Authentication ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Enterprise Login")
    u = st.selectbox("Select Employee", list(db["users"].keys()))
    p = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if db["users"][u]["pass"] == p:
            st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
            if u in db.get("drafts", {}):
                for key, val in db["drafts"][u].items():
                    if key == 'exp_list': st.session_state.exp_list = val
                    else: st.session_state[key] = val
            db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
            save_db(db); st.rerun()
        else: st.error("Wrong Password")

else:
    # --- 4. Sidebar & Management ---
    with st.sidebar:
        st.header(f"Employee: {st.session_state['user']}")
        user_node = db["users"][st.session_state['user']]
        
        if st.session_state['role'] != 'admin':
            st.divider()
            st.markdown("### 💳 Financial Status")
            net_val = user_node['salary'] + user_node['bonus'] - user_node['advances'] - user_node['deductions']
            st.write(f"Basic: {user_node['salary']} | Net: **{net_val} LE**")

        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Management Panel")
            m_mode = st.radio("Select Tool", ["Payroll Center", "Employee Management", "Branch Management", "Task Management", "Shift History"])
            
            if m_mode == "Payroll Center":
                st.subheader("Salary Management")
                emp = st.selectbox("Select Employee", [u for u in db["users"].keys() if u != 'admin'])
                u_d = db["users"][emp]
                c1, c2 = st.columns(2)
                with c1:
                    db["users"][emp]["salary"] = st.number_input("Monthly Salary", value=float(u_d['salary']))
                    adv = st.number_input("Add Advance", 0.0)
                    ded = st.number_input("Add Deduction", 0.0)
                with c2:
                    bon = st.number_input("Add Bonus", 0.0)
                    off = st.number_input("Off Days", 0)
                    if st.button("Update Financials"):
                        db["users"][emp]["advances"] += adv
                        db["users"][emp]["deductions"] += ded
                        db["users"][emp]["bonus"] += bon
                        db["users"][emp]["off_days"] += off
                        save_db(db); st.success("Updated!"); st.rerun()
                
                net = u_d['salary'] + u_d['bonus'] - u_d['advances'] - u_d['deductions']
                st.metric("Current Net Balance", f"{net} LE")
                
                # PDF Generation Logic
                buf = io.BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=letter)
                elements = [Paragraph(f"Salary Slip: {emp} - {datetime.now().strftime('%Y-%m')}", getSampleStyleSheet()['Title'])]
                t_data = [["Category", "Value"], ["Basic Salary", u_d['salary']], ["Advances", u_d['advances']], ["Deductions", u_d['deductions']], ["Bonus", u_d['bonus']], ["Final Net", net]]
                tbl = Table(t_data, colWidths=[200, 100])
                tbl.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke)]))
                elements.append(tbl)
                doc.build(elements)
                st.download_button(f"📥 Download PDF for {emp}", buf.getvalue(), f"Salary_{emp}.pdf")

                if st.button("Close Month (Reset Balances)"):
                    db["users"][emp].update({"advances": 0, "deductions": 0, "bonus": 0, "off_days": 0})
                    save_db(db); st.success("Month Closed"); st.rerun()

            elif m_mode == "Employee Management":
                with st.expander("Add New Employee"):
                    nu = st.text_input("New Username")
                    np = st.text_input("New Password")
                    if st.button("Create"):
                        db["users"][nu] = {"pass": np, "role": "user", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0}
                        save_db(db); st.rerun()
                target = st.selectbox("Select to Delete", list(db["users"].keys()))
                if st.button("Delete User") and target != 'admin':
                    del db["users"][target]; save_db(db); st.rerun()

            elif m_mode == "Branch Management":
                nb = st.text_input("New Branch")
                if st.button("Add"): db["branches"].append(nb); save_db(db); st.rerun()
                rem_b = st.selectbox("Remove Branch", db["branches"])
                if st.button("Remove"): db["branches"].remove(rem_b); save_db(db); st.rerun()

    # --- 5. Main Dashboard ---
    st.title("📊 Shift Control Dashboard")
    colA, colB, colC = st.columns(3)
    with colA: branch = st.selectbox("Branch", db["branches"])
    with colB: shift = st.selectbox("Shift", ["Morning", "Evening", "Full"])
    with colC: st.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    t1, t2, t3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])

    with t1:
        st.subheader("Opening Details")
        for task in db["tasks"]["opening"]: st.checkbox(task, key=f"s_{task}", on_change=sync_draft)
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Cash Counter**")
            o_total = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                o_total += st.number_input(f"{d} LE", 0, key=f"o_{d}", on_change=sync_draft) * d
            o_coins = st.number_input("Coins", 0.0, key="oc", on_change=sync_draft)
            st.success(f"Total Opening Cash: {o_total + o_coins}")
        with c2:
            st.write("**Counters & Debit**")
            ks = st.number_input("Kyocera Start", 0, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start", 0, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Start", 0.0, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit In", 0.0, key="u10_val", on_change=sync_draft)

    with t2:
        st.subheader("Closing Details")
        for task in db["tasks"]["closing"]: st.checkbox(task, key=f"e_{task}", on_change=sync_draft)
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write("**Sales & Expenses**")
            sys_s = st.number_input("System Sales", 0.0, key="c_sys_sales", on_change=sync_draft)
            e_cat = st.selectbox("Exp Category", db["exp_categories"])
            e_val = st.number_input("Exp Amount", 0.0, key="cur_e")
            if st.button("Add Expense"):
                st.session_state.exp_list.append({"Type": e_cat, "Amount": e_val})
                sync_draft(); st.rerun()
            total_e = sum(x['Amount'] for x in st.session_state.exp_list)
            st.write(f"Total Expenses: {total_e}")
            if st.button("Clear Expenses"): st.session_state.exp_list = []; sync_draft(); st.rerun()

        with c2:
            st.write("**Cash & Match**")
            c_total = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                c_total += st.number_input(f"{d} LE ", 0, key=f"c_{d}", on_change=sync_draft) * d
            c_coins = st.number_input("Coins ", 0.0, key="cc", on_change=sync_draft)
            v22 = st.number_input("Debit Out", 0.0, key="v22_val", on_change=sync_draft)
            
            drawer_c = c_total + c_coins
            expected = (o_total + o_coins) + sys_s + u10 - total_e - v22
            diff = drawer_c - expected
            st.metric("Expected Cash", expected, delta=diff)

        with c3:
            st.write("**Printers Details**")
            ke = st.number_input("Kyocera End", 0, key="k1end", on_change=sync_draft)
            k_os = st.number_input("K-One Side", 0, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("K-Duplex", 0, key="k1dp", on_change=sync_draft)
            k_er = st.number_input("K-Errors", 0, key="k1err", on_change=sync_draft)
            st.write(f"K-Used: {ke-ks} | K-Acc: {k_os + (k_dp*2) + k_er}")
            st.divider()
            xe = st.number_input("Xerox End", 0, key="x2end", on_change=sync_draft)
            x_os = st.number_input("X-One Side", 0, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("X-Duplex", 0, key="x2dp", on_change=sync_draft)
            x_er = st.number_input("X-Errors", 0, key="x2err", on_change=sync_draft)
            st.write(f"X-Used: {xe-xs} | X-Acc: {x_os + (x_dp*2) + x_er}")

    with t3:
        st.subheader("Social Media Tasks")
        for task in db["tasks"]["social"]: st.checkbox(task, key=f"m_{task}", on_change=sync_draft)

    # --- 6. Submit ---
    st.divider()
    if st.button("🏁 FINISH SHIFT & ARCHIVE", use_container_width=True):
        arc = {"date": str(datetime.now().date()), "staff": st.session_state['user'], "branch": branch, "sales": sys_s, "diff": diff}
        db["history"].append(arc); save_db(db); st.success("Shift Saved!"); st.rerun()

    wa_msg = f"*NMS REPORT*\nStaff: {st.session_state['user']}\nSales: {sys_s}\nDiff: {diff}"
    wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; font-weight:bold;">📱 WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
