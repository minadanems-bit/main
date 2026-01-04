import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import io
from PIL import Image as PILImage

# --- 1. إعدادات الصفحة والهوية ---
st.set_page_config(page_title="NMS ERP System", layout="wide")

DB_FILE = 'nms_db.json'

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "id_num": "000"}
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

db = load_data()

# --- 2. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP System - Login")
    
    # رفع اللوجو في صفحة الدخول
    logo_file = st.file_uploader("Upload Company Logo (Optional)", type=['png', 'jpg', 'jpeg'], key="main_logo")
    if logo_file:
        st.image(logo_file, width=150)
        st.session_state['logo'] = logo_file.getvalue()

    user_choice = st.selectbox("Employee Select", list(db["users"].keys()))
    pwd = st.text_input("Password", type="password")
    
    if st.button("Login", use_container_width=True):
        if db["users"][user_choice]["pass"] == pwd:
            st.session_state.update({'logged_in': True, 'user': user_choice, 'role': db["users"][user_choice]["role"]})
            st.rerun()
        else:
            st.error("Incorrect Password")
else:
    # --- 3. القائمة الجانبية (Sidebar) ---
    with st.sidebar:
        if 'logo' in st.session_state:
            st.image(st.session_state['logo'], width=100)
        st.header(f"Welcome, {st.session_state['user']}")
        
        # رفع الصورة الشخصية للموظف
        emp_photo = st.file_uploader("Upload Your Photo", type=['jpg', 'png'])
        if emp_photo:
            st.image(emp_photo, caption="Employee Photo", width=100)
            
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Control Panel")
            with st.expander("Add New Employee"):
                new_u = st.text_input("Username (Login)")
                new_p = st.text_input("Password")
                f_name = st.text_input("Full Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone Number")
                address = st.text_input("Address")
                id_card = st.text_input("ID Number")
                if st.button("Register Employee"):
                    db["users"][new_u] = {
                        "pass": new_p, "role": "user", "full_name": f_name,
                        "email": email, "phone": phone, "address": address, "id_num": id_card
                    }
                    save_data(db)
                    st.success(f"Employee {new_u} added!")

    # --- 4. واجهة البرنامج الرئيسية ---
    st.title("📋 Daily Shift Management")
    
    # Shift Header Info
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with c2: st.info(f"🌞 **Day:** {datetime.now().strftime('%A')}")
    with c3: branch = st.selectbox("Branch", db["branches"])
    with c4: shift = st.selectbox("Shift Type", ["Morning", "Between", "Night"])

    t1, t2, t3 = st.tabs(["🟢 Tab 1: Start Shift", "🔴 Tab 2: End Shift", "📱 Tab 3: Marketing"])

    # --- TAB 1: START ---
    with t1:
        col_chk, col_cash, col_print = st.columns([1, 1, 1])
        with col_chk:
            st.subheader("✅ Start Checklist")
            start_checks = {task: st.checkbox(task, key=f"s_{task}") for task in db["tasks"]["start"]}
        
        with col_cash:
            st.subheader("💰 Opening Cash")
            denoms = [200, 100, 50, 20, 10, 5]
            open_vals = {}
            total_open = 0
            for d in denoms:
                open_vals[d] = st.number_input(f"{d} LE", step=1, key=f"o_{d}")
                total_open += (open_vals[d] * d)
            o_coins = st.number_input("Coins", step=1, key="o_coins")
            total_open += o_coins
            st.markdown(f"**Total Opening: {total_open} LE**")

        with col_print:
            st.subheader("🖨️ Opening Counters")
            k_start = st.number_input("Kyocera Start Counter", step=1)
            x_start = st.number_input("Xerox Start Counter", step=1)
            opay_start = st.number_input("Opay Opening Balance", step=1)

    # --- TAB 2: END ---
    with t2:
        col_chk2, col_cash2, col_print2 = st.columns([1, 1, 1])
        with col_chk2:
            st.subheader("✅ End Checklist")
            end_checks = {task: st.checkbox(task, key=f"e_{task}") for task in db["tasks"]["end"]}
            st.subheader("💳 Non-Cash Transactions")
            v_pay = st.number_input("Instapay", step=1)
            w_pay = st.number_input("Wallet", step=1)
            visa_pay = st.number_input("Visa", step=1)

        with col_cash2:
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in denoms:
                v = st.number_input(f"{d} LE ", step=1, key=f"c_{d}")
                total_close += (v * d)
            c_coins = st.number_input("Coins ", step=1, key="c_coins")
            total_close += c_coins
            expenses = st.number_input("Expenses (المصاريف)", step=1)
            # الربط الحسابي
            net_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Difference", f"{net_diff} LE", delta_color="inverse")

        with col_print2:
            st.subheader("🖨️ Final Counters & Usage")
            k_end = st.number_input("Kyocera End Counter", step=1)
            x_end = st.number_input("Xerox End Counter", step=1)
            total_printed = (k_end - k_start) + (x_end - x_start)
            st.write(f"Total Pages Printed: **{total_printed}**")
            
            os_side = st.number_input("One Side Pages", step=1)
            duplex = st.number_input("Duplex Pages", step=1)
            draft = st.number_input("Draft Pages", step=1)
            
            st.divider()
            opay_end = st.number_input("Opay Closing Balance", step=1)
            st.write(f"Opay Difference: **{opay_end - opay_start} LE**")

    # --- TAB 3: MARKETING ---
    with t3:
        st.subheader("📱 Social Media Tasks")
        m_cols = st.columns(4)
        m_tasks_status = {}
        for i, task in enumerate(db["tasks"]["marketing"]):
            m_tasks_status[task] = m_cols[i % 4].checkbox(task, key=f"m_{task}")

    # --- 5. استخراج التقرير PDF ---
    st.divider()
    if st.button("📥 Generate & Download Professional PDF Report", type="primary", use_container_width=True):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # العنوان واللوجو في PDF
        elements.append(Paragraph(f"Shift Report: {branch}", styles['Title']))
        elements.append(Paragraph(f"Employee: {st.session_state['user']} | Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # جدول البيانات المالية
        report_data = [
            ["Category", "Details", "Amount"],
            ["Cash", "Opening Total", f"{total_open} LE"],
            ["", "Closing Total", f"{total_close} LE"],
            ["", "Expenses", f"{expenses} LE"],
            ["", "Net Difference", f"{net_diff} LE"],
            ["Printers", "Total Printed", f"{total_printed} Pages"],
            ["", "One Side / Duplex / Draft", f"{os_side} / {duplex} / {draft}"],
            ["Opay", "Opay Difference", f"{opay_end - opay_start} LE"],
            ["Non-Cash", "Visa/Wallet/Instapay", f"{visa_pay + w_pay + v_pay} LE"]
        ]
        t = Table(report_data, colWidths=[100, 200, 100])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke)]))
        elements.append(t)
        
        doc.build(elements)
        st.download_button("Download Report", data=buffer.getvalue(), file_name=f"NMS_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
        st.balloons()
