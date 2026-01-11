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
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0, "phone": "", "address": "", "id_num": "", "start_date": "", "email": "", "marital_status": "", "education": "", "military_status": "", "photo": None}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار", "كهرباء ومياه"],
            "tasks": {
                "opening": ["Fingerprint", "Power On"],
                "closing": ["Cleaned", "Power Off"],
                "social": ["WhatsApp Story", "Facebook Post"],
                "interaction": ["Like", "Share"]
            },
            "logs": [], "drafts": {}, "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        # ضمان وجود كل الحقول الجديدة في بيانات الموظفين القدامى
        new_fields = ["salary", "advances", "deductions", "bonus", "off_days", "phone", "address", "id_num", "start_date", "email", "marital_status", "education", "military_status"]
        for u in data["users"]:
            for field in new_fields:
                if field not in data["users"][u]: data["users"][u][field] = "" if "salary" not in field else 0
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & Session Logic ---
st.set_page_config(page_title="NMS Enterprise ERP", layout="wide")

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

# --- 3. Login System ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Enterprise Login")
    u = st.selectbox("Select Employee", list(db["users"].keys()))
    p = st.text_input("Password", type="password")
    if st.button("Login to System", use_container_width=True):
        if db["users"][u]["pass"] == p:
            st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
            if u in db.get("drafts", {}):
                for key, val in db["drafts"][u].items():
                    if key == 'exp_list': st.session_state.exp_list = val
                    else: st.session_state[key] = val
            save_db(db); st.rerun()
        else: st.error("Authentication Failed")

else:
    # --- 4. Sidebar & Admin Logic ---
    with st.sidebar:
        st.header(f"Welcome, {st.session_state['user']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Control Panel")
            admin_mode = st.radio("Management", ["HR (Employees)", "Financial (Payroll)", "Branches", "Tasks", "Expenses Types", "History"])
            
            # --- HR: Manage Employees (Add/Edit/Delete) ---
            if admin_mode == "HR (Employees)":
                st.subheader("👥 Employee Records")
                action = st.radio("Action", ["Add New", "Edit/Update", "Delete"], horizontal=True)
                
                if action == "Add New":
                    with st.form("add_user"):
                        nu = st.text_input("Username")
                        np = st.text_input("Password")
                        n_name = st.text_input("Full Name")
                        if st.form_submit_button("Create Account"):
                            db["users"][nu] = {"pass": np, "role": "user", "full_name": n_name}
                            save_db(db); st.success("Created!"); st.rerun()
                
                elif action == "Edit/Update":
                    target = st.selectbox("Select Employee to Edit", list(db["users"].keys()))
                    u_node = db["users"][target]
                    c1, c2 = st.columns(2)
                    with c1:
                        u_node["full_name"] = st.text_input("Full Name", u_node.get("full_name", ""))
                        u_node["pass"] = st.text_input("Password", u_node["pass"])
                        u_node["phone"] = st.text_input("Mobile Number", u_node.get("phone", ""))
                        u_node["email"] = st.text_input("Email", u_node.get("email", ""))
                        u_node["address"] = st.text_area("Address", u_node.get("address", ""))
                    with c2:
                        u_node["id_num"] = st.text_input("ID / National ID", u_node.get("id_num", ""))
                        u_node["start_date"] = st.text_input("Start Working Date", u_node.get("start_date", ""))
                        u_node["marital_status"] = st.selectbox("Marital Status", ["Single", "Married", "Divorced"], index=0)
                        u_node["education"] = st.text_input("Education Degree", u_node.get("education", ""))
                        u_node["military_status"] = st.text_input("Military Status", u_node.get("military_status", ""))
                    if st.button("💾 Save All Details"):
                        db["users"][target] = u_node
                        save_db(db); st.success("Profile Updated!")

                elif action == "Delete":
                    target = st.selectbox("Select to Remove", [u for u in db["users"].keys() if u != 'admin'])
                    if st.button("🗑️ Permanently Delete"):
                        del db["users"][target]; save_db(db); st.rerun()

            # --- Manage Branches ---
            elif admin_mode == "Branches":
                st.subheader("🏢 Branch Management")
                new_br = st.text_input("Add Branch Name")
                if st.button("Add"): db["branches"].append(new_br); save_db(db); st.rerun()
                rem_br = st.selectbox("Select Branch to Delete", db["branches"])
                if st.button("Delete"): db["branches"].remove(rem_br); save_db(db); st.rerun()

            # --- Manage Tasks ---
            elif admin_mode == "Tasks":
                st.subheader("📝 Task Management")
                t_cat = st.selectbox("Category", ["Opening", "Closing", "Social", "Interaction"])
                new_t = st.text_input(f"New {t_cat} Task")
                if st.button("Add Task"): db["tasks"][t_cat.lower()].append(new_t); save_db(db); st.rerun()
                rem_t = st.selectbox("Select Task to Remove", db["tasks"][t_cat.lower()])
                if st.button("Remove Task"): db["tasks"][t_cat.lower()].remove(rem_t); save_db(db); st.rerun()

            # --- Manage Expense Types ---
            elif admin_mode == "Expenses Types":
                st.subheader("💰 Expense Categories")
                new_ex = st.text_input("New Type")
                if st.button("Add Type"): db["exp_categories"].append(new_ex); save_db(db); st.rerun()
                rem_ex = st.selectbox("Delete Type", db["exp_categories"])
                if st.button("Delete"): db["exp_categories"].remove(rem_ex); save_db(db); st.rerun()

            # --- Payroll Center ---
            elif admin_mode == "Financial (Payroll)":
                st.subheader("💳 Salaries & Payroll")
                emp = st.selectbox("Select Employee", [u for u in db["users"].keys() if u != 'admin'])
                u_f = db["users"][emp]
                c1, c2 = st.columns(2)
                with c1:
                    u_f["salary"] = st.number_input("Basic Salary", value=float(u_f.get("salary", 0)))
                    add_adv = st.number_input("Add Advance", 0.0)
                    add_ded = st.number_input("Add Deduction", 0.0)
                with c2:
                    add_bon = st.number_input("Add Bonus", 0.0)
                    if st.button("Update Financials"):
                        u_f["advances"] += add_adv
                        u_f["deductions"] += add_ded
                        u_f["bonus"] += add_bon
                        save_db(db); st.success("Updated!")
                
                net = u_f["salary"] + u_f["bonus"] - u_f["advances"] - u_f["deductions"]
                st.metric(f"Net for {emp}", f"{net:,.2f} LE")
                if st.button("Reset Month (Clear All)"):
                    u_f.update({"advances": 0, "deductions": 0, "bonus": 0}); save_db(db); st.rerun()

    # --- 5. Main Dashboard (Mina's Approved Workflow) ---
    st.title("📊 Daily Shift Control")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with inf2: st.info(f"🕒 **Day:** {datetime.now().strftime('%A')}")
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL & SUBMIT"])

    with tab1:
        st.subheader("Opening Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", 0, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            t_open += st.number_input("Coins", 0.0, key="oc", on_change=sync_draft)
            st.success(f"Total: {t_open:,.2f}")
        with c3:
            ks = st.number_input("Kyocera Opening", 0, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Opening", 0, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Start", 0.0, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit Received", 0.0, key="u10_val", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            sys_sales = st.number_input("System Sales", 0.0, key="c_sys_sales", on_change=sync_draft)
            v22 = st.number_input("Debit Pending", 0.0, key="v22_val", on_change=sync_draft)
            t_e_pay = st.number_input("Instapay", 0.0, key="c_insta") + st.number_input("Wallet/Visa", 0.0, key="c_wall")
        with c2:
            st.write("**Expenses**")
            e_cat = st.selectbox("Category", db["exp_categories"])
            e_val = st.number_input("Amount", 0.0, key="cur_e")
            if st.button("Add Exp"):
                st.session_state.exp_list.append({"Type": e_cat, "Amount": e_val})
                sync_draft(); st.rerun()
            expenses = sum(x['Amount'] for x in st.session_state.exp_list)
            st.write(f"Total: {expenses}")
            st.divider()
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                t_close += st.number_input(f"{d} LE ", 0, key=f"c_{d}", on_change=sync_draft) * d
            t_close += st.number_input("Coins ", 0.0, key="cc", on_change=sync_draft)
            expected = t_open + sys_sales + u10 - expenses - v22 - t_e_pay
            st.metric("Expected", f"{expected:,.2f}", delta=f"{t_close - expected:,.2f}")
        with c3:
            ke = st.number_input("Kyocera End", 0, key="k1end", on_change=sync_draft)
            xe = st.number_input("Xerox End", 0, key="x2end", on_change=sync_draft)
            st.write(f"K-Used: {ke-ks} | X-Used: {xe-xs}")

    with tab3:
        st.subheader("Social Media & Finalize")
        for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        st.divider()
        # --- الأزرار مجمعة في آخر صفحة كما طلبت يا مينا ---
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("🏁 ARCHIVE SHIFT", use_container_width=True):
                arc = {"date": str(datetime.now().date()), "staff": st.session_state['user'], "branch": branch, "sales": sys_sales, "net_diff": t_close - expected}
                db["history"].append(arc); db["pending_debit"] = v22
                db["drafts"][st.session_state['user']] = {}; st.session_state.exp_list = []
                save_db(db); st.success("Shift Archived!"); st.rerun()
        with col_s2:
            if st.button("📥 GENERATE PDF", use_container_width=True):
                buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=letter); elements = []
                elements.append(Paragraph(f"NMS Report: {branch}", getSampleStyleSheet()['Title']))
                t1 = Table([["Sales", sys_sales], ["Expenses", expenses], ["Drawer", t_close]], colWidths=[150, 100])
                t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
                elements.append(t1); doc.build(elements)
                st.download_button("💾 Download Report", buf.getvalue(), f"NMS_{branch}.pdf")
        with col_s3:
            wa_msg = f"*NMS REPORT*\n*Branch:* {branch}\n*Sales:* {sys_sales}\n*Diff:* {t_close - expected}"
            wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📱 WHATSAPP</button></a>', unsafe_allow_html=True)
