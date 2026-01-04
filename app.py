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

# --- 1. Settings & Persistence ---
DB_FILE = 'nms_db.json'
MANAGER_PHONE = "+971522045638" # ضع رقمك هنا بيبدأ بـ 20

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "phone": "000", "id_num": "000", "address": "HQ", "email": "admin@nms.com", "photo": None},
                "Mina": {"pass": "1234", "role": "user", "full_name": "Mina", "photo": None},
                "Youstina": {"pass": "1234", "role": "user", "full_name": "Youstina", "photo": None},
                "Mark": {"pass": "1234", "role": "user", "full_name": "Mark", "photo": None},
                "Fatma": {"pass": "1234", "role": "user", "full_name": "Fatma", "photo": None}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger print", "Power on", "Uniform and name tag", "Music on", "Paper loaded", "Cash counted", "All good"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Finger print", "Report sent"],
                "marketing": ["Canva 1", "Canva 2", "WhatsApp story", "WhatsApp channel", "FB story", "FB post/reel", "FB group", "Page story", "Page post/reel", "Threads", "Instagram story", "Instagram post/reel", "TikTok story", "TikTok post", "Telegram story", "Telegram channel", "LinkedIn post", "Like", "Love", "Care", "Share"]
            }
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def img_to_b64(file):
    if file: return base64.b64encode(file.getvalue()).decode()
    return None

db = load_data()

# --- 2. Page Setup ---
st.set_page_config(page_title="NMS ERP System", layout="wide")
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# --- 3. Login ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP System - Login")
    col1, col2 = st.columns(2)
    with col1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=200)
        logo_up = st.file_uploader("Upload Company Logo", type=['png', 'jpg'])
        if st.button("Save Logo"):
            db["logo"] = img_to_b64(logo_up); save_data(db); st.rerun()
    with col2:
        u_choice = st.selectbox("Select User", list(db["users"].keys()))
        p_input = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if db["users"][u_choice]["pass"] == p_input:
                st.session_state.update({'logged_in': True, 'user': u_choice, 'role': db["users"][u_choice]["role"]})
                st.rerun()
            else: st.error("Wrong Password")

else:
    # --- 4. Sidebar ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=100)
        st.header(f"Welcome, {st.session_state['user']}")
        user_info = db["users"][st.session_state['user']]
        if user_info.get("photo"): st.image(base64.b64decode(user_info["photo"]), width=150)
        p_up = st.file_uploader("Update Personal Photo", type=['png', 'jpg'])
        if st.button("Save Photo"):
            db["users"][st.session_state['user']]["photo"] = img_to_b64(p_up); save_data(db); st.rerun()
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ Manager Dashboard")
            admin_opt = st.radio("Action", ["Edit/Delete Employee", "Add New User"])
            if admin_opt == "Edit/Delete Employee":
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                db["users"][target]["full_name"] = st.text_input("Full Name", db["users"][target].get("full_name", ""))
                db["users"][target]["phone"] = st.text_input("Mobile", db["users"][target].get("phone", ""))
                db["users"][target]["pass"] = st.text_input("Password", db["users"][target].get("pass", ""))
                col_save, col_del = st.columns(2)
                if col_save.button("Save Changes"): save_data(db); st.success("Updated!")
                if col_del.button("Delete User", type="primary"):
                    if target != "admin": del db["users"][target]; save_data(db); st.rerun()
            else:
                nu = st.text_input("New Username")
                np = st.text_input("New Password")
                if st.button("Create"):
                    db["users"][nu] = {"pass": np, "role": "user", "full_name": nu}; save_data(db); st.rerun()

    # --- 5. Main Content ---
    st.title("📋 Daily Operational Report")
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')} | **{datetime.now().strftime('%A')}**")
    with c2: branch = st.selectbox("Select Branch", db["branches"])
    with c3: shift = st.selectbox("Select Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: START", "🔴 TAB 2: END", "📱 TAB 3: MARKETING"])

    with tab1:
        col_chk, col_cash, col_op = st.columns(3)
        with col_chk:
            st.subheader("Start Checklist")
            for t in db["tasks"]["start"]: st.checkbox(t, key=f"s_{t}")
        with col_cash:
            st.subheader("💰 Opening Cash")
            total_open = 0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, format="%d", key=f"o_{d}")
                total_open += (v * d)
            o_coins = st.number_input("Opening Coins", step=1, format="%d", key="oc")
            total_open += o_coins
            st.metric("Total Opening Cash", f"{total_open} LE")
        with col_op:
            st.subheader("🖨️ Opening Data")
            k_start = st.number_input("Kyocera Start Counter", step=1, format="%d")
            x_start = st.number_input("Xerox Start Counter", step=1, format="%d")
            opay_start = st.number_input("Opay Opening Balance", step=1, format="%d")

    with tab2:
        col_chk2, col_cash2, col_pr2 = st.columns(3)
        with col_chk2:
            st.subheader("End Checklist")
            for t in db["tasks"]["end"]: st.checkbox(t, key=f"e_{t}")
            st.divider(); st.subheader("💳 Non-Cash")
            instapay = st.number_input("Instapay", step=1, format="%d")
            wallet = st.number_input("Wallet", step=1, format="%d")
            visa = st.number_input("Visa", step=1, format="%d")
        with col_cash2:
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, format="%d", key=f"c_{d}")
                total_close += (v * d)
            c_coins = st.number_input("Closing Coins", step=1, format="%d", key="cc")
            total_close += c_coins
            exp = st.number_input("Expenses", step=1, format="%d")
            net_diff = (total_close + exp) - total_open
            st.metric("Cash Balance", f"{net_diff} LE")
        with col_pr2:
            st.subheader("🖨️ Printer Usage")
            st.write("**Kyocera**")
            k_end = st.number_input("Kyocera Final Counter", step=1, format="%d")
            k_1 = st.number_input("Kyo One-Side", step=1, format="%d", key="k1")
            k_2 = st.number_input("Kyo Duplex", step=1, format="%d", key="k2")
            k_3 = st.number_input("Kyo Draft", step=1, format="%d", key="k3")
            k_counter_change = k_end - k_start
            k_manual = k_1 + (k_2 * 2) + k_3
            
            st.write("**Xerox**")
            x_end = st.number_input("Xerox Final Counter", step=1, format="%d")
            x_1 = st.number_input("Xero One-Side", step=1, format="%d", key="x1")
            x_2 = st.number_input("Xero Duplex", step=1, format="%d", key="x2")
            x_3 = st.number_input("Xero Draft", step=1, format="%d", key="x3")
            x_counter_change = x_end - x_start
            x_manual = x_1 + (x_2 * 2) + x_3
            
            st.divider(); opay_end = st.number_input("Opay Final Balance", step=1, format="%d")

    with tab3:
        st.subheader("📱 Marketing Checklist")
        m_cols = st.columns(4)
        m_results = {task: m_cols[i%4].checkbox(task, key=f"m_{task}") for i, task in enumerate(db["tasks"]["marketing"])}

    # --- 6. Buttons ---
    st.divider()
    cw1, cw2 = st.columns(2)
    with cw1:
        if st.button("📥 Generate PDF Report", use_container_width=True):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"NMS Report - {branch}", styles['Title']))
            data = [["Category", "Detail", "Value"], ["Cash", "Net Diff", f"{net_diff} LE"], ["Kyo", "Usage", f"{k_manual}"], ["Xerox", "Usage", f"{x_manual}"]]
            t = Table(data, colWidths=[100, 200, 100])
            t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
            elements.append(t); doc.build(elements)
            st.download_button("Download Now", data=buffer.getvalue(), file_name=f"NMS_Report.pdf")

    with cw2:
        wa_text = f"*🚀 NMS SHIFT REPORT*\nBranch: {branch}\nUser: {st.session_state['user']}\nCash Diff: {net_diff} LE\nKyo Usage: {k_manual}\nXerox Usage: {x_manual}\nOpay Diff: {opay_end-opay_start} LE"
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_text)}"
        # السطر المصلح أدناه:
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer;">📱 Send WhatsApp Report</button></a>', unsafe_allow_html=True)
