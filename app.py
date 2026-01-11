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
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager"}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform", "Cash Counted"],
                "closing": ["Cleaned", "Power Off", "Report Sent"],
                "social": ["WhatsApp Story", "Facebook Post", "Instagram"],
                "interaction": ["Like", "Share"]
            },
            "logs": [], "drafts": {}, "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        # التأكد من وجود كل الحقول الجديدة للموظفين
        fields = ["salary", "advances", "deductions", "bonus", "phone", "address", "id_num", "start_date", "email", "marital_status", "education", "military_status"]
        for u in data["users"]:
            for field in fields:
                if field not in data["users"][u]: data["users"][u][field] = "" if "salary" not in field else 0.0
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Logic & Sessions ---
st.set_page_config(page_title="NMS Enterprise ERP", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})
if 'exp_list' not in st.session_state:
    st.session_state.exp_list = []

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # حفظ كل المدخلات التي تبدأ برموز معينة لضمان عدم ضياع البيانات
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_'))}
        current_data['exp_list'] = st.session_state.exp_list
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# --- 3. Login ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Login")
    u = st.selectbox("Select Employee", list(db["users"].keys()))
    p = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if db["users"][u]["pass"] == p:
            st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
            if u in db.get("drafts", {}):
                for key, val in db["drafts"][u].items():
                    if key == 'exp_list': st.session_state.exp_list = val
                    else: st.session_state[key] = val
            save_db(db); st.rerun()
        else: st.error("Wrong Password")
else:
    # --- 4. Sidebar (Admin Control Panel) ---
    with st.sidebar:
        st.header(f"👤 {st.session_state['user']}")
        if st.button("Logout"): st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            adm = st.radio("Management", ["HR", "Branches", "Tasks", "Expenses", "Finance", "History"])
            
            if adm == "HR":
                action = st.radio("Action", ["Add", "Edit", "Delete"], horizontal=True)
                if action == "Add":
                    with st.form("new_user"):
                        nu = st.text_input("Username")
                        np = st.text_input("Password")
                        if st.form_submit_button("Create"):
                            db["users"][nu] = {"pass": np, "role": "user"}
                            save_db(db); st.rerun()
                elif action == "Edit":
                    target = st.selectbox("Select Employee", list(db["users"].keys()))
                    u_node = db["users"][target]
                    u_node["pass"] = st.text_input("Password", u_node["pass"])
                    u_node["phone"] = st.text_input("Phone", u_node.get("phone", ""))
                    u_node["address"] = st.text_input("Address", u_node.get("address", ""))
                    u_node["id_num"] = st.text_input("ID Number", u_node.get("id_num", ""))
                    u_node["start_date"] = st.text_input("Start Date", u_node.get("start_date", ""))
                    u_node["military_status"] = st.text_input("Military", u_node.get("military_status", ""))
                    if st.button("Update Profile"): save_db(db); st.success("Updated")
                elif action == "Delete":
                    target = st.selectbox("Delete Employee", [u for u in db["users"].keys() if u != 'admin'])
                    if st.button("Confirm Delete"): del db["users"][target]; save_db(db); st.rerun()

            elif adm == "Branches":
                new_b = st.text_input("Branch Name")
                if st.button("Add"): db["branches"].append(new_b); save_db(db); st.rerun()
                del_b = st.selectbox("Remove Branch", db["branches"])
                if st.button("Remove"): db["branches"].remove(del_b); save_db(db); st.rerun()

    # --- 5. Main Dashboard ---
    st.title("📊 Daily Shift")
    branch = st.selectbox("Branch", db["branches"])
    shift = st.selectbox("Shift", ["Morning", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL & FINALIZE"])

    with tab1:
        if db.get("pending_debit", 0) > 0:
            st.warning(f"⚠️ Pending Debit: {db['pending_debit']:,.2f} LE")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = sum([st.number_input(f"{d} LE", 0, key=f"o_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
            t_open += st.number_input("Coins", 0.0, key="oc", on_change=sync_draft)
            st.success(f"Total Opening: {t_open:,.2f}")
        with c3:
            ks = st.number_input("Kyocera Start", 0, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start", 0, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Start", 0.0, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit Received", 0.0, key="u10_val", on_change=sync_draft)

    with tab2:
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            sys_sales = st.number_input("System Sales", 0.0, key="c_sys_sales", on_change=sync_draft)
            v22 = st.number_input("Debit Pending (Out)", 0.0, key="v22_val", on_change=sync_draft)
            # فصل فيزا عن المحفظة
            insta = st.number_input("Instapay", 0.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", 0.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", 0.0, key="c_visa", on_change=sync_draft)
            total_digital = insta + wallet + visa
        with c2:
            st.write("**Expenses**")
            e_cat = st.selectbox("Category", db["exp_categories"])
            e_val = st.number_input("Amount", 0.0, key="cur_e")
            if st.button("Add Exp"):
                st.session_state.exp_list.append({"Type": e_cat, "Amount": e_val})
                sync_draft(); st.rerun()
            expenses = sum(x['Amount'] for x in st.session_state.exp_list)
            st.divider()
            t_close = sum([st.number_input(f"{d} LE ", 0, key=f"c_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
            t_close += st.number_input("Closing Coins", 0.0, key="cc", on_change=sync_draft)
            expected = t_open + sys_sales + u10 - expenses - v22 - total_digital
            st.metric("Expected", f"{expected:,.2f}", delta=f"{t_close - expected:,.2f}")
        with c3:
            # دمج عدادات الطباعة الدقيقة
            st.markdown("### 🖨️ Kyocera Details")
            ke = st.number_input("Counter End", 0, key="k1end", on_change=sync_draft)
            k_os = st.number_input("One-Side", 0, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("Duplex", 0, key="k1dp", on_change=sync_draft)
            k_err = st.number_input("Errors", 0, key="k1err", on_change=sync_draft)
            k_actual = ke - ks
            st.caption(f"Used: {k_actual} | Accounted: {k_os + (k_dp*2) + k_err}")
            
            st.markdown("### 🖨️ Xerox Details")
            xe = st.number_input("Counter End (X)", 0, key="x2end", on_change=sync_draft)
            x_os = st.number_input("One-Side (X)", 0, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("Duplex (X)", 0, key="x2dp", on_change=sync_draft)
            x_actual = xe - xs
            
            st.divider()
            ope = st.number_input("Opay Final Balance", 0.0, key="op_end", on_change=sync_draft)
            st.write(f"Opay Movement: {ops - ope:,.2f}")

    with tab3:
        st.subheader("Social Media Tasks")
        for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        st.divider()
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("🏁 ARCHIVE SHIFT", use_container_width=True):
                arc = {"date": str(datetime.now().date()), "staff": st.session_state['user'], "branch": branch, "sales": sys_sales, "net_diff": t_close - expected, "expenses": expenses}
                db["history"].append(arc); db["pending_debit"] = v22
                db["drafts"][st.session_state['user']] = {}; st.session_state.exp_list = []
                save_db(db); st.success("Archived!"); st.rerun()
        with col_s2:
            if st.button("📥 DOWNLOAD PDF", use_container_width=True):
                st.write("Generating PDF...") # يمكن إضافة كود ReportLab هنا
        with col_s3:
            wa_msg = f"*NMS REPORT*\n*Branch:* {branch}\n*Sales:* {sys_sales}\n*Expenses:* {expenses}\n*Short/Plus:* {t_close - expected}"
            wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📱 WHATSAPP</button></a>', unsafe_allow_html=True)
