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

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="NMS Shift System v2", layout="wide")

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
                "start": ["Finger print", "Power on", "Uniform and name tag", "Music on", "Paper loaded", "Cash counted", "All good"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Finger print", "Report sent"],
                "marketing": [
                    "Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "FB Story", "FB Post/Reel", 
                    "FB Group", "Page Story", "Page Post/Reel", "Threads", "Instagram Story", 
                    "Instagram Post/Reel", "TikTok Story", "TikTok Post", "Telegram Story", 
                    "Telegram Channel", "LinkedIn Post", "Like", "Love", "Care", "Share"
                ]
            }
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_data, f)
        return default_data
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

db = load_data()

# --- وظيفة إنشاء PDF ---
def create_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Shift Report: {data['branch']}", styles['Title']))
    elements.append(Paragraph(f"Employee: {data['user']} | Date: {data['date']} | Shift: {data['shift']}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # ملخص الحسابات
    table_data = [
        ["Category", "Details", "Value"],
        ["Financial", "Opening Cash", f"{data['total_open']} LE"],
        ["", "Closing Cash", f"{data['total_close']} LE"],
        ["", "Expenses", f"{data['expenses']} LE"],
        ["", "Net Difference", f"{data['net_diff']} LE"],
        ["Printers", "Total Printed", f"{data['total_printed']} pages"],
        ["Opay", "Opay Difference", f"{data['opay_diff']} LE"]
    ]
    t = Table(table_data)
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.grey)]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- واجهة تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 NMS Management System")
    user_choice = st.selectbox("Select Employee", list(db["users"].keys()))
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if db["users"][user_choice]["pass"] == pwd:
            st.session_state['logged_in'] = True
            st.session_state['user'] = user_choice
            st.session_state['role'] = db["users"][user_choice]["role"]
            st.rerun()
        else: st.error("Wrong password")
else:
    # --- القائمة الجانبية ---
    with st.sidebar:
        st.header(f"Welcome, {st.session_state['user']}")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("Admin Panel")
            u_n = st.text_input("New Employee")
            u_p = st.text_input("New Pass")
            if st.button("Add"):
                db["users"][u_n] = {"pass": u_p, "role": "user"}
                save_data(db); st.success("Added")

    # --- الجزء العلوي (Shift Info) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        st.write(f"**Day:** {datetime.now().strftime('%A')}")
    with col2:
        branch = st.selectbox("Branch", db["branches"])
    with col3:
        shift_time = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 Tab 1: Start Shift", "🔴 Tab 2: End Shift", "📱 Tab 3: Marketing"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Checklist (Start)")
            start_done = [st.checkbox(t, key=f"start_{t}") for t in db["tasks"]["start"]]
            
            st.subheader("💰 Opening Cash")
            denoms = [200, 100, 50, 20, 10, 5]
            total_open = 0
            for d in denoms:
                v = st.number_input(f"{d} LE", step=1, format="%d", key=f"open_{d}")
                total_open += (v * d)
            o_coins = st.number_input("Coins", step=1, format="%d", key="open_coins")
            total_open += o_coins
            st.info(f"Total Opening: {total_open} LE")

        with c2:
            st.subheader("🖨️ Printer & Opay Start")
            k_start = st.number_input("Kyocera Opening Counter", step=1, format="%d")
            x_start = st.number_input("Xerox Opening Counter", step=1, format="%d")
            opay_start = st.number_input("Opay Opening Balance", step=1, format="%d")

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Checklist (End)")
            end_done = [st.checkbox(t, key=f"end_{t}") for t in db["tasks"]["end"]]
            
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in denoms:
                v = st.number_input(f"{d} LE ", step=1, format="%d", key=f"close_{d}")
                total_close += (v * d)
            c_coins = st.number_input("Coins ", step=1, format="%d", key="close_coins")
            total_close += c_coins
            expenses = st.number_input("Expenses (المصاريف)", step=1, format="%d")
            
            # الربط الحسابي
            net_diff = (total_close + expenses) - total_open
            st.metric("Net Difference (الفرق الصافي)", f"{net_diff} LE")

        with c2:
            st.subheader("📊 Usage & Non-Cash")
            k_end = st.number_input("Kyocera Final Counter", step=1, format="%d")
            x_end = st.number_input("Xerox Final Counter", step=1, format="%d")
            
            st.write(f"Total Printed: {(k_end - k_start) + (x_end - x_start)}")
            one_side = st.number_input("One Side", step=1, format="%d")
            duplex = st.number_input("Duplex", step=1, format="%d")
            draft = st.number_input("Draft", step=1, format="%d")
            
            st.divider()
            opay_end = st.number_input("Opay Closing Balance", step=1, format="%d")
            st.write(f"Opay Difference: {opay_end - opay_start}")
            
            st.subheader("💳 Non-Cash")
            instapay = st.number_input("Instapay", step=1, format="%d")
            wallet = st.number_input("Wallet", step=1, format="%d")
            visa = st.number_input("Visa", step=1, format="%d")

    with tab3:
        st.subheader("📱 Marketing Checklist")
        cols = st.columns(3)
        for i, task in enumerate(db["tasks"]["marketing"]):
            cols[i % 3].checkbox(task, key=f"mkt_{task}")

    st.divider()
    if st.button("📥 Generate Final Report & PDF", type="primary"):
        report_data = {
            "branch": branch, "user": st.session_state['user'], "date": datetime.now().strftime('%Y-%m-%d'),
            "shift": shift_time, "total_open": total_open, "total_close": total_close,
            "expenses": expenses, "net_diff": net_diff, "total_printed": (k_end-k_start)+(x_end-x_start),
            "opay_diff": opay_end - opay_start
        }
        pdf = create_pdf(report_data)
        st.download_button("Click here to Download PDF", data=pdf, file_name="shift_report.pdf", mime="application/pdf")
        st.balloons()
