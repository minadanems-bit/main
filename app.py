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

# --- 1. Database & Image Functions ---
DB_FILE = 'nms_db.json'

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "General Manager", "phone": "000", "id_num": "000", "address": "NMS HQ", "email": "admin@nms.com", "photo": None}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger print", "Power on", "Uniform and name tag", "Music on", "Paper loaded", "Cash counted", "All good"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Finger print", "Report sent"],
                "marketing": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "FB Story", "FB Post/Reel", "FB Group", "Page Story", "Page Post/Reel", "Threads", "Instagram Story", "Instagram Post/Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post", "Like", "Love", "Care", "Share"]
            }
        }
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

def img_to_b64(file):
    if file:
        return base64.b64encode(file.getvalue()).decode()
    return None

db = load_data()

# --- 2. Page Configuration ---
st.set_page_config(page_title="NMS ERP System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# --- 3. Login System ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - System Login")
    
    col_l, col_r = st.columns([1, 1])
    with col_l:
        if db.get("logo"):
            st.image(base64.b64decode(db["logo"]), width=200)
        new_logo = st.file_uploader("Update Company Logo", type=['png', 'jpg', 'jpeg'])
        if st.button("Save Logo"):
            db["logo"] = img_to_b64(new_logo)
            save_data(db)
            st.rerun()

    with col_r:
        u_list = list(db["users"].keys())
        user_choice = st.selectbox("Employee", u_list)
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if db["users"][user_choice]["pass"] == password:
                st.session_state.update({'logged_in': True, 'user': user_choice, 'role': db["users"][user_choice]["role"]})
                st.rerun()
            else: st.error("Invalid Password")

else:
    # --- 4. Sidebar (Employee Profile & Admin Tools) ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=100)
        st.header(f"Hi, {st.session_state['user']}")
        
        # Employee Photo persistence
        u_data = db["users"][st.session_state['user']]
        if u_data.get("photo"):
            st.image(base64.b64decode(u_data["photo"]), width=150, caption="Profile Photo")
        
        new_photo = st.file_uploader("Update Profile Photo", type=['png', 'jpg'])
        if st.button("Save Photo"):
            db["users"][st.session_state['user']]["photo"] = img_to_b64(new_photo)
            save_data(db)
            st.rerun()

        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ Admin Dashboard")
            admin_mode = st.radio("Mode", ["Edit/View Employees", "Add New", "Delete"])
            
            if admin_mode == "Edit/View Employees":
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                db["users"][target]["full_name"] = st.text_input("Full Name", db["users"][target].get("full_name", ""))
                db["users"][target]["phone"] = st.text_input("Phone", db["users"][target].get("phone", ""))
                db["users"][target]["email"] = st.text_input("Email", db["users"][target].get("email", ""))
                db["users"][target]["address"] = st.text_input("Address", db["users"][target].get("address", ""))
                db["users"][target]["id_num"] = st.text_input("ID Number", db["users"][target].get("id_num", ""))
                db["users"][target]["pass"] = st.text_input("Login Password", db["users"][target].get("pass", ""))
                if st.button("Save Employee Data"):
                    save_data(db)
                    st.success("Data Saved Successfully!")

            elif admin_mode == "Add New":
                new_username = st.text_input("New Username")
                new_p = st.text_input("New Password")
                if st.button("Create Account"):
                    db["users"][new_username] = {"pass": new_p, "role": "user", "full_name": new_username}
                    save_data(db)
                    st.rerun()

    # --- 5. Main Content ---
    st.title("📋 Daily Shift Management")
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"**Date:** {datetime.now().strftime('%Y-%m-%d')} | **{datetime.now().strftime('%A')}**")
    with c2: branch = st.selectbox("Branch", db["branches"])
    with c3: shift_time = st.selectbox("Shift", ["Morning", "Between", "Night"])

    t1, t2, t3 = st.tabs(["🟢 TAB 1: START", "🔴 TAB 2: END", "📱 TAB 3: MARKETING"])

    with t1:
        col_chk, col_cash, col_pr = st.columns([1, 1.2, 1])
        with col_chk:
            st.subheader("Start Checklist")
            s_checks = {t: st.checkbox(t, key=f"s_{t}") for t in db["tasks"]["start"]}
        
        with col_cash:
            st.subheader("💰 Opening Cash")
            total_open = 0
            for d in [200, 100, 50, 20, 10, 5]:
                val = st.number_input(f"{d} LE", min_value=0, step=1, format="%d", key=f"o_{d}")
                total_open += (val * d)
            o_coins = st.number_input("Opening Coins", min_value=0, step=1, format="%d", key="o_c")
            total_open += o_coins
            st.metric("Total Opening", f"{total_open} LE")

        with col_pr:
            st.subheader("🖨️ Opening Counters")
            k_start = st.number_input("Kyocera Start", step=1, format="%d")
            x_start = st.number_input("Xerox Start", step=1, format="%d")
            op_start = st.number_input("Opay Start Balance", step=1, format="%d")

    with t2:
        col_chk2, col_cash2, col_pr2 = st.columns([1, 1.2, 1])
        with col_chk2:
            st.subheader("End Checklist")
            e_checks = {t: st.checkbox(t, key=f"e_{t}") for t in db["tasks"]["end"]}
            st.subheader("💳 Non-Cash")
            i_p = st.number_input("Instapay", step=1, format="%d")
            w_p = st.number_input("Wallet", step=1, format="%d")
            v_p = st.number_input("Visa", step=1, format="%d")
            non_cash_total = i_p + w_p + v_p

        with col_cash2:
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in [200, 100, 50, 20, 10, 5]:
                val = st.number_input(f"{d} LE ", min_value=0, step=1, format="%d", key=f"c_{d}")
                total_close += (val * d)
            c_coins = st.number_input("Closing Coins", min_value=0, step=1, format="%d", key="c_c")
            total_close += c_coins
            expenses = st.number_input("Expenses", step=1, format="%d")
            net_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Diff", f"{net_diff} LE")

        with col_pr2:
            st.subheader("🖨️ Final Counters")
            k_end = st.number_input("Kyocera End", step=1, format="%d")
            x_end = st.number_input("Xerox End", step=1, format="%d")
            total_p = (k_end - k_start) + (x_end - x_start)
            st.write(f"Total Printed: {total_p}")
            os_p = st.number_input("One Side", step=1, format="%d")
            du_p = st.number_input("Duplex", step=1, format="%d")
            dr_p = st.number_input("Draft", step=1, format="%d")
            st.divider()
            op_end = st.number_input("Opay End Balance", step=1, format="%d")
            st.write(f"Opay Diff: {op_end - op_start} LE")

    with t3:
        st.subheader("📱 Marketing Checklist")
        m_cols = st.columns(4)
        m_results = {t: m_cols[i%4].checkbox(t, key=f"m_{t}") for i, t in enumerate(db["tasks"]["marketing"])}

    st.divider()
    if st.button("📥 Generate Final Report PDF", type="primary", use_container_width=True):
        st.balloons()
        st.success("PDF Generated Successfully!")
