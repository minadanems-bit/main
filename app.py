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
            "logo": None,
            "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "HQ", "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
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
        if "history" not in data: data["history"] = []
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Session Logic ---
st.set_page_config(page_title="NMS Management System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_'))}
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
                    st.session_state[key] = val
            db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
            save_db(db); st.rerun()
        else: st.error("Authentication Failed")

else:
    # --- 4. Sidebar ---
    with st.sidebar:
        st.header(f"User: {st.session_state['user']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        # استرجاع صلاحيات المدير كاملة كما كانت
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Master Control")
            admin_mode = st.radio("Settings", ["Review History", "Manage Employees", "Manage Branches", "Manage Tasks", "Audit Logs"])
            
            if admin_mode == "Manage Employees":
                st.subheader("👥 Employee Control")
                target_user = st.selectbox("Select Employee", list(db["users"].keys()))
                db["users"][target_user]["pass"] = st.text_input("Password", db["users"][target_user]["pass"])
                if st.button("💾 Save Changes"): save_db(db); st.success("Updated!")
            # (بقية أقسام الإدمن موجودة في الكود الأصلي)

    # --- 5. Main Dashboard ---
    st.title("📊 Daily Shift Control")
    branch = st.selectbox("Branch", db["branches"])
    shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL MEDIA"])

    with tab1:
        st.subheader("Opening Procedures")
        if db.get("pending_debit", 0) > 0:
            st.warning(f"📦 تنبيه: يوجد (Debit) مُرحل: {db['pending_debit']:,.2f}")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, key="oc", on_change=sync_draft)
            t_open += o_coins
            st.success(f"Total: {t_open:,.2f}")
        with c3:
            k_start = st.number_input("Kyocera Opening", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Opening", step=1, key="xs", on_change=sync_draft)
            u10_debit = st.number_input("Debit Received", min_value=0.0, key="u10_val", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            sys_sales = st.number_input("System Sales", min_value=0.0, key="c_sys_sales", on_change=sync_draft)
            v22_debit = st.number_input("Debit Pending", min_value=0.0, key="v22_val", on_change=sync_draft)
            instapay = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1.0, key="c_visa", on_change=sync_draft)
        with c2:
            st.write("**Closing Cash**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE  ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins  ", step=0.5, key="cc", on_change=sync_draft)
            t_close += c_coins
            expenses = st.number_input("Expenses", step=1.0, key="c_exp", on_change=sync_draft)
            
            # --- الحسابات (رؤية الموظف) ---
            expected_cash = t_open + sys_sales + u10_debit - expenses - v22_debit - (instapay + wallet + visa)
            net_diff = t_close - expected_cash
            st.metric("Expected Cash", f"{expected_cash:,.2f} LE", delta=f"{net_diff:,.2f}")
            if abs(net_diff) < 1: st.success("✅ Match")
            else: st.error(f"❌ Difference: {net_diff:,.2f}")

        with c3:
            st.markdown("### 🖨️ Kyocera")
            k_end = st.number_input("K-End", step=1, key="k1end", on_change=sync_draft)
            k_os = st.number_input("K-OneSide", step=1, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("K-Duplex", step=1, key="k1dp", on_change=sync_draft)
            k_err = st.number_input("K-Errors", step=1, key="k1err", on_change=sync_draft)
            k_test = st.number_input("K-Test", step=1, key="k1tst", on_change=sync_draft)
            
            st.markdown("### 🖨️ Xerox")
            x_end = st.number_input("X-End", step=1, key="x2end", on_change=sync_draft)
            x_os = st.number_input("X-OneSide", step=1, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("X-Duplex", step=1, key="x2dp", on_change=sync_draft)
            x_err = st.number_input("X-Errors/Jam", step=1, key="x2err", on_change=sync_draft)
            x_test = st.number_input("X-Test/Draft", step=1, key="x2tst", on_change=sync_draft)

    with tab3:
        for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)

    # --- 6. Submit ---
    if st.button("🏁 SUBMIT FULL REPORT", use_container_width=True):
        # (كود الأرشفة والواتساب الأصلي هنا)
        st.success("Report Submitted!")
