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

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMS Shift System", layout="wide")

DB_FILE = 'nms_db.json'

# --- 2. وظائف قاعدة البيانات ---
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

# --- 3. وظيفة إنشاء PDF ---
def create_pdf(report_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"Shift Report - {report_data['branch']}", styles['Title']))
    elements.append(Paragraph(f"Date: {report_data['date']} | Day: {report_data['day']}", styles['Normal']))
    elements.append(Paragraph(f"Employee: {report_data['user']} | Shift: {report_data['shift']}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    data = [
        ["Category", "Details", "Value"],
        ["Cash", "Total Opening", f"{report_data['total_open']} LE"],
        ["", "Total Closing", f"{report_data['total_close']} LE"],
        ["", "Expenses", f"{report_data['expenses']} LE"],
        ["", "Net Cash Diff", f"{report_data['net_diff']} LE"],
        ["Printers", "Total Pages", f"{report_data['total_pages']}"],
        ["Opay", "Opay Diff", f"{report_data['opay_diff']} LE"],
        ["Non-Cash", "Total (Visa/Wallet)", f"{report_data['non_cash']} LE"]
    ]
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- 4. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 NMS Management System")
    user_choice = st.selectbox("Select Employee", list(db["users"].keys()))
    pwd = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        if db["users"][user_choice]["pass"] == pwd:
            st.session_state['logged_in'] = True
            st.session_state['user'] = user_choice
            st.session_state['role'] = db["users"][user_choice]["role"]
            st.rerun()
        else:
            st.error("Wrong Password!")
else:
    # --- القائمة الجانبية ---
    with st.sidebar:
        st.header(f"👤 {st.session_state['user']}")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("Admin Tools")
            new_user = st.text_input("New Employee Name")
            new_pass = st.text_input("New Password")
            if st.button("Add Employee"):
                db["users"][new_user] = {"pass": new_pass, "role": "user"}
                save_data(db)
                st.success("Employee Added!")

    # --- Shift Info (تلقائي) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        st.write(f"**Day:** {datetime.now().strftime('%A')}")
    with col2:
        branch = st.selectbox("Branch", db["branches"])
    with col3:
        shift_time = st.selectbox("Shift", ["Morning", "Between", "Night"])

    # --- التبويبات (Tabs) ---
    tab1, tab2, tab3 = st.tabs(["🟢 Start Shift", "🔴 End Shift", "📱 Marketing"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Checklist")
            for t in db["tasks"]["start"]: st.checkbox(t, key=f"s_{t}")
            
            st.subheader("💰 Opening Cash")
            total_open = 0
            denoms = [200, 100, 50, 20, 10, 5]
            for d in denoms:
                val = st.number_input(f"{d} LE", step=1, format="%d", key=f"o_{d}")
                total_open += (val * d)
            o_coins = st.number_input("Coins", step=1, format="%d", key="o_c")
            total_open += o_coins
            st.info(f"Total Opening Cash: {total_open} LE")
        
        with c2:
            st.subheader("🖨️ Opening Counters")
            k_start = st.number_input("Kyocera Counter (Start)", step=1, format="%d")
            x_start = st.number_input("Xerox Counter (Start)", step=1, format="%d")
            opay_start = st.number_input("Opay Balance (Start)", step=1, format="%d")

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Checklist")
            for t in db["tasks"]["end"]: st.checkbox(t, key=f"e_{t}")
            
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in denoms:
                val = st.number_input(f"{d} LE ", step=1, format="%d", key=f"c_{d}")
                total_close += (val * d)
            c_coins = st.number_input("Coins ", step=1, format="%d", key="c_c")
            total_close += c_coins
            expenses = st.number_input("Expenses (المصاريف)", step=1, format="%d")
            
            net_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Difference", f"{net_diff} LE")

        with c2:
            st.subheader("📊 Usage Details")
            k_end = st.number_input("Kyocera Counter (End)", step=1, format="%d")
            x_end = st.number_input("Xerox Counter (End)", step=1, format="%d")
            
            printed = (k_end - k_start) + (x_end - x_start)
            st.write(f"**Total Printed Pages:** {printed}")
            
            col_pr1, col_pr2, col_pr3 = st.columns(3)
            with col_pr1: one_side = st.number_input("One Side", step=1)
            with col_pr2: duplex = st.number_input("Duplex", step=1)
            with col_pr3: draft = st.number_input("Draft", step=1)
            
            st.divider()
            opay_end = st.number_input("Opay Balance (End)", step=1, format="%d")
            st.write(f"**Opay Difference:** {opay_end - opay_start}")
            
            st.subheader("💳 Non-Cash Transactions")
            i_pay = st.number_input("Instapay", step=1)
            wallet = st.number_input("Wallet", step=1)
            visa = st.number_input("Visa", step=1)
            total_non_cash = i_pay + wallet + visa

    with tab3:
        st.subheader("📱 Marketing Checklist")
        m_cols = st.columns(3)
        for i, m_task in enumerate(db["tasks"]["marketing"]):
            m_cols[i % 3].checkbox(m_task, key=f"m_{m_task}")

    # --- زر الاستخراج ---
    st.divider()
    if st.button("📥 Generate Report & Download PDF", type="primary", use_container_width=True):
        report_data = {
            "branch": branch, "user": st.session_state['user'], "date": datetime.now().strftime('%Y-%m-%d'),
            "day": datetime.now().strftime('%A'), "shift": shift_time, "total_open": total_open,
            "total_close": total_close, "expenses": expenses, "net_diff": net_diff,
            "total_pages": (k_end - k_start) + (x_end - x_start), "opay_diff": opay_end - opay_start,
            "non_cash": total_non_cash
        }
        pdf_file = create_pdf(report_data)
        st.download_button("Download Report PDF", data=pdf_file, file_name=f"Report_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
        st.balloons()
