import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. Database & Persistence Logic ---
DB_FILE = 'nms_db.json'

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "General Manager", "phone": "000", "id_num": "000", "address": "NMS HQ", "email": "admin@nms.com", "photo": None},
                "Mina": {"pass": "1234", "role": "user", "full_name": "Mina", "photo": None}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger print", "Power on", "Uniform", "Music on", "Paper loaded", "Cash counted"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Report sent"],
                "marketing": ["WhatsApp Story", "FB Post", "Instagram", "TikTok", "LinkedIn", "Telegram"]
            }
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def img_to_b64(file):
    if file: return base64.b64encode(file.getvalue()).decode()
    return None

db = load_data()

# --- 2. Page Configuration ---
st.set_page_config(page_title="NMS ERP System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# --- 3. Login Page ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - System Login")
    col_l, col_r = st.columns(2)
    with col_l:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=200)
        logo_up = st.file_uploader("Upload Company Logo", type=['png', 'jpg'])
        if st.button("Save Logo"):
            db["logo"] = img_to_b64(logo_up)
            save_data(db); st.rerun()
    with col_r:
        u_choice = st.selectbox("Select Employee", list(db["users"].keys()))
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
        st.header(f"User: {st.session_state['user']}")
        user_info = db["users"][st.session_state['user']]
        if user_info.get("photo"): st.image(base64.b64decode(user_info["photo"]), width=150)
        photo_up = st.file_uploader("Change Photo", type=['png', 'jpg'])
        if st.button("Save My Photo"):
            db["users"][st.session_state['user']]["photo"] = img_to_b64(photo_up)
            save_data(db); st.rerun()
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ Admin")
            target_u = st.selectbox("Edit Employee", list(db["users"].keys()))
            db["users"][target_u]["full_name"] = st.text_input("Full Name", db["users"][target_u].get("full_name", ""))
            db["users"][target_u]["pass"] = st.text_input("Password", db["users"][target_u].get("pass", ""))
            if st.button("Save Updates"): save_data(db); st.success("Updated")

    # --- 5. Main Content ---
    st.title("📋 Daily Operations")
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"**Date:** {datetime.now().strftime('%Y-%m-%d')} | **{datetime.now().strftime('%A')}**")
    with c2: branch = st.selectbox("Branch", db["branches"])
    with c3: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    t1, t2, t3 = st.tabs(["🟢 START", "🔴 END", "📱 MARKETING"])

    with t1:
        col_c, col_k, col_x = st.columns(3)
        with col_c:
            st.subheader("Cash Opening")
            total_open = 0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, format="%d", key=f"o_{d}")
                total_open += (v * d)
            o_coins = st.number_input("Opening Coins", step=1, format="%d", key="oc")
            total_open += o_coins
        with col_k:
            st.subheader("Kyocera Start")
            k_start = st.number_input("Counter Start", step=1, format="%d", key="ks")
            op_start = st.number_input("Opay Start Balance", step=1, format="%d", key="os")
        with col_x:
            st.subheader("Xerox Start")
            x_start = st.number_input("Xerox Counter Start", step=1, format="%d", key="xs")

    with t2:
        col_c2, col_k2, col_x2 = st.columns(3)
        with col_c2:
            st.subheader("Cash Closing")
            total_close = 0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, format="%d", key=f"c_{d}")
                total_close += (v * d)
            c_coins = st.number_input("Closing Coins", step=1, format="%d", key="cc")
            total_close += c_coins
            exp = st.number_input("Expenses", step=1, format="%d")
            st.metric("Net Cash Diff", f"{(total_close + exp) - total_open} LE")
        with col_k2:
            st.subheader("Kyocera Closing")
            k_end = st.number_input("Kyocera Final Counter", step=1, format="%d")
            k_os = st.number_input("Kyo One-Side", step=1, format="%d", key="kos")
            k_dup = st.number_input("Kyo Duplex", step=1, format="%d", key="kdup")
            k_usage = (k_end - k_start)
            k_calc = k_os + (k_dup * 2)
            st.warning(f"Kyo Diff: {k_calc - k_usage}")
        with col_x2:
            st.subheader("Xerox Closing")
            x_end = st.number_input("Xerox Final Counter", step=1, format="%d")
            x_os = st.number_input("Xerox One-Side", step=1, format="%d", key="xos")
            x_dup = st.number_input("Xerox Duplex", step=1, format="%d", key="xdup")
            x_usage = (x_end - x_start)
            x_calc = x_os + (x_dup * 2)
            st.warning(f"Xerox Diff: {x_calc - x_usage}")
            op_end = st.number_input("Opay Final", step=1, format="%d")

    with t3:
        st.subheader("Marketing Tasks")
        m_cols = st.columns(4)
        m_data = {}
        for i, task in enumerate(db["tasks"]["marketing"]):
            m_data[task] = m_cols[i % 4].checkbox(task, key=f"m_{task}")

    st.divider()
    if st.button("📥 EXPORT FINAL PDF REPORT", type="primary", use_container_width=True):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"NMS Report - {branch}", styles['Title']))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')} | User: {st.session_state['user']}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Financial Table
        data = [["Item", "Value"], ["Opening Cash", f"{total_open} LE"], ["Closing Cash", f"{total_close} LE"], ["Expenses", f"{exp} LE"], ["Net Diff", f"{(total_close + exp)-total_open} LE"], ["Opay Diff", f"{op_end-op_start} LE"]]
        t = Table(data, colWidths=[200, 200])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t)
        
        doc.build(elements)
        st.download_button("Download Report PDF", data=buffer.getvalue(), file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
