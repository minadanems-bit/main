import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# إعدادات الصفحة
st.set_page_config(page_title="NMS Shift System", layout="wide")

DB_FILE = 'nms_db.json'

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        default_data = {
            "users": {
                "admin": {"pass": "admin123", "role": "admin"},
                "Mina": {"pass": "1234", "role": "user"},
                "Youstina": {"pass": "1234", "role": "user"},
                "Mark": {"pass": "1234", "role": "user"},
                "Fatma": {"pass": "1234", "role": "user"}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger Print", "Power On", "Uniform", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "end": ["Contacts", "Place Cleaned", "Power Off", "Cash Counted", "Finger Print", "Report Sent"],
                "marketing": ["Canva 1", "Canva 2", "WhatsApp Story", "FB Story", "TikTok Post", "Instagram Reel"]
            }
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_data, f)
        return default_data
    
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            os.remove(DB_FILE) # لو الملف بايظ نمسحه ونعيد التحميل
            return load_data()

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

db = load_data()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- Login System ---
if not st.session_state['logged_in']:
    st.title("🔐 NMS Shift System Login")
    user_choice = st.selectbox("Select Employee", list(db["users"].keys()))
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if db["users"][user_choice]["pass"] == password:
            st.session_state['logged_in'] = True
            st.session_state['user'] = user_choice
            st.session_state['role'] = db["users"][user_choice]["role"]
            st.rerun()
        else:
            st.error("Wrong Password!")

else:
    # --- Sidebar ---
    with st.sidebar:
        st.header(f"Hi, {st.session_state['user']}")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("Admin Tools")
            new_u = st.text_input("New Name")
            new_p = st.text_input("New Pass")
            if st.button("Add Employee"):
                db["users"][new_u] = {"pass": new_p, "role": "user"}
                save_data(db)
                st.success("Added!")

    # --- Main App ---
    col1, col2, col3 = st.columns(3)
    with col1: st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with col2: branch = st.selectbox("Branch", db["branches"])
    with col3: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 Start Shift", "🔴 End Shift", "📱 Marketing"])

    with tab1:
        st.subheader("Opening Checklist")
        s_tasks = [st.checkbox(t, key=f"s_{t}") for t in db["tasks"]["start"]]
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💰 Opening Cash")
            denoms = [200, 100, 50, 20, 10, 5]
            total_open = 0
            for d in denoms:
                v = st.number_input(f"{d} LE", step=1, key=f"o_{d}", format="%d")
                total_open += (v * d)
            coins = st.number_input("Coins", step=1, key="o_coins", format="%d")
            total_open += coins
            st.info(f"Total Opening: {total_open}")
        with c2:
            st.subheader("🖨️ Initial Counters")
            k_start = st.number_input("Kyocera Start", step=1, format="%d")
            x_start = st.number_input("Xerox Start", step=1, format="%d")
            opay_start = st.number_input("Opay Balance Start", step=1, format="%d")

    with tab2:
        st.subheader("Closing Report")
        e_tasks = [st.checkbox(t, key=f"e_{t}") for t in db["tasks"]["end"]]
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in denoms:
                v = st.number_input(f"{d} LE ", step=1, key=f"c_{d}", format="%d")
                total_close += (v * d)
            coins_c = st.number_input("Coins ", step=1, key="c_coins", format="%d")
            total_close += coins_c
            expenses = st.number_input("Expenses (مصاريف)", step=1, format="%d")
            net_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Diff", f"{net_diff} LE")
        with c2:
            st.subheader("🖨️ Usage & Opay")
            k_end = st.number_input("Kyocera End", step=1, format="%d")
            x_end = st.number_input("Xerox End", step=1, format="%d")
            st.write(f"Total Printed: {(k_end - k_start) + (x_end - x_start)}")
            opay_end = st.number_input("Opay Balance End", step=1, format="%d")
            st.write(f"Opay Diff: {opay_end - opay_start}")

    with tab3:
        st.subheader("Marketing Tasks")
        m_tasks = [st.checkbox(t, key=f"m_{t}") for t in db["tasks"]["marketing"]]

    st.divider()
    if st.button("Generate Final Report", type="primary"):
        st.balloons()
        st.success("Report generated! (You can add PDF logic here later)")
