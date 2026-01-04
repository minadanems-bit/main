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
                "Mina": {"pass": "1234", "role": "user", "full_name": "Mina", "photo": None},
                "Youstina": {"pass": "1234", "role": "user", "full_name": "Youstina", "photo": None},
                "Mark": {"pass": "1234", "role": "user", "full_name": "Mark", "photo": None},
                "Fatma": {"pass": "1234", "role": "user", "full_name": "Fatma", "photo": None}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger print", "Power on", "Uniform and name tag", "Music on", "Paper loaded", "Cash counted", "All good"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Finger print", "Report sent"],
                "marketing": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "FB Story", "FB Post/Reel", "FB Group", "Page Story", "Page Post/Reel", "Threads", "Instagram Story", "Instagram Post/Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post", "Like", "Love", "Care", "Share"]
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
        st.header(f"Hi, {st.session_state['user']}")
        user_info = db["users"][st.session_state['user']]
        if user_info.get("photo"): st.image(base64.b64decode(user_info["photo"]), width=150)
        photo_up = st.file_uploader("Upload Profile Photo", type=['png', 'jpg'])
        if st.button("Save Photo"):
            db["users"][st.session_state['user']]["photo"] = img_to_b64(photo_up)
            save_data(db); st.rerun()
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ Manager Panel")
            target_u = st.selectbox("Select Employee to Edit", list(db["users"].keys()))
            db["users"][target_u]["full_name"] = st.text_input("Full Name", db["users"][target_u].get("full_name", ""))
            db["users"][target_u]["phone"] = st.text_input("Mobile", db["users"][target_u].get("phone", ""))
            db["users"][target_u]["email"] = st.text_input("Email", db["users"][target_u].get("email", ""))
            db["users"][target_u]["address"] = st.text_input("Address", db["users"][target_u].get("address", ""))
            db["users"][target_u]["id_num"] = st.text_input("ID Number", db["users"][target_u].get("id_num", ""))
            db["users"][target_u]["pass"] = st.text_input("Password", db["users"][target_u].get("pass", ""))
            if st.button("Save Employee Data"): save_data(db); st.success("Employee data updated!")

    # --- 5. Main App Content ---
    st.title("📋 Daily Operations Report")
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"**Date:** {datetime.now().strftime('%Y-%m-%d')} | **{datetime.now().strftime('%A')}**")
    with c2: branch = st.selectbox("Branch", db["branches"])
    with c3: shift_type = st.selectbox("Shift", ["Morning", "Between", "Night"])

    t1, t2, t3 = st.tabs(["🟢 TAB 1: START", "🔴 TAB 2: END", "📱 TAB 3: MARKETING"])

    with t1:
        col_chk, col_cash, col_op = st.columns([1, 1, 1])
        with col_chk:
            st.subheader("Start Checklist")
            for t in db["tasks"]["start"]: st.checkbox(t, key=f"s_{t}")
        with col_cash:
            st.subheader("💰 Opening Cash")
            total_open = 0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, format="%d", key=f"o_{d}")
                total_open += (v * d)
            o_coins = st.number_input("Coins", step=1, format="%d", key="o_c")
            total_open += o_coins
            st.metric("Total Opening Cash", f"{total_open} LE")
        with col_op:
            st.subheader("🖨️ Opening Counters")
            k_start = st.number_input("Kyocera Start Counter", step=1, format="%d")
            x_start = st.number_input("Xerox Start Counter", step=1, format="%d")
            opay_start = st.number_input("Opay Opening Balance", step=1, format="%d")

    with t2:
        col_chk2, col_cash2, col_pr2 = st.columns([1, 1, 1])
        with col_chk2:
            st.subheader("End Checklist")
            for t in db["tasks"]["end"]: st.checkbox(t, key=f"e_{t}")
            st.divider()
            st.subheader("💳 Non-Cash Transactions")
            instapay = st.number_input("Instapay", step=1, format="%d")
            wallet = st.number_input("Wallet", step=1, format="%d")
            visa = st.number_input("Visa", step=1, format="%d")

        with col_cash2:
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, format="%d", key=f"c_{d}")
                total_close += (v * d)
            c_coins = st.number_input("Coins ", step=1, format="%d", key="c_c")
            total_close += c_coins
            expenses = st.number_input("Expenses", step=1, format="%d")
            # Linking Calculation
            net_cash_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Difference", f"{net_cash_diff} LE")

        with col_pr2:
            st.subheader("🖨️ Printer Usage & Matching")
            st.markdown("--- **Kyocera Tracking** ---")
            k_end = st.number_input("Kyocera Final Counter", step=1, format="%d")
            k_oneside = st.number_input("Kyocera One Side", step=1, format="%d", key="k1")
            k_duplex = st.number_input("Kyocera Duplex", step=1, format="%d", key="k2")
            k_draft = st.number_input("Kyocera Draft", step=1, format="%d", key="k3")
            k_diff_counter = k_end - k_start
            k_calc_total = k_oneside + (k_duplex * 2) + k_draft
            st.info(f"Kyo Counter Change: {k_diff_counter} | Manual Total: {k_calc_total}")
            
            st.markdown("--- **Xerox Tracking** ---")
            x_end = st.number_input("Xerox Final Counter", step=1, format="%d")
            x_oneside = st.number_input("Xerox One Side", step=1, format="%d", key="x1")
            x_duplex = st.number_input("Xerox Duplex", step=1, format="%d", key="x2")
            x_draft = st.number_input("Xerox Draft", step=1, format="%d", key="x3")
            x_diff_counter = x_end - x_start
            x_calc_total = x_oneside + (x_duplex * 2) + x_draft
            st.info(f"Xerox Counter Change: {x_diff_counter} | Manual Total: {x_calc_total}")
            
            st.divider()
            st.subheader("💳 Opay Closing")
            opay_end = st.number_input("Opay Closing Balance", step=1, format="%d")
            st.write(f"Opay Difference: {opay_end - opay_start} LE")

    with t3:
        st.subheader("📱 Marketing Checklist")
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["marketing"]):
            m_cols[i % 4].checkbox(task, key=f"m_{task}")

    st.divider()
    if st.button("📥 DOWNLOAD COMPLETE PDF REPORT", type="primary", use_container_width=True):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"NMS Shift Report: {branch}", styles['Title']))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')} | User: {st.session_state['user']} | Shift: {shift_type}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        report_data = [
            ["Section", "Description", "Value"],
            ["Cash", "Opening Total", f"{total_open} LE"],
            ["Cash", "Closing Total", f"{total_close} LE"],
            ["Cash", "Expenses", f"{expenses} LE"],
            ["Cash", "Net Difference", f"{net_cash_diff} LE"],
            ["Printers", "Kyocera Total (Counter)", f"{k_diff_counter}"],
            ["Printers", "Xerox Total (Counter)", f"{x_diff_counter}"],
            ["Opay", "Balance Difference", f"{opay_end - opay_start} LE"],
            ["Non-Cash", "Visa/Wallet/Instapay", f"{visa+wallet+instapay} LE"]
        ]
        t = Table(report_data, colWidths=[100, 200, 100])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t)
        doc.build(elements)
        st.download_button("Click here to Download PDF", data=buffer.getvalue(), file_name=f"Report_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
        st.balloons()
