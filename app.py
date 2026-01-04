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
DB_FILE = 'nms_system_db.json'
MANAGER_PHONE = "+971522045638" # قم بتغيير هذا الرقم لرقمك الخاص

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "General Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "NMS HQ", "photo": None},
                "Mina": {"pass": "1234", "role": "user", "full_name": "Mina", "photo": None},
                "Youstina": {"pass": "1234", "role": "user", "full_name": "Youstina", "photo": None},
                "Mark": {"pass": "1234", "role": "user", "full_name": "Mark", "photo": None},
                "Fatma": {"pass": "1234", "role": "user", "full_name": "Fatma", "photo": None}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger print", "Power on", "Uniform and name tag", "Music on", "Paper loaded", "Cash counted", "All good"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Finger print", "Report sent"],
                "marketing": [
                    "Canva 1", "Canva 2", "WhatsApp story", "WhatsApp channel", "FB story", 
                    "FB post/reel", "FB group", "Page story", "Page post/reel", "Threads", 
                    "Instagram story", "Instagram post/reel", "TikTok story", "TikTok post", 
                    "Telegram story", "Telegram channel", "LinkedIn post", "Like", "Love", "Care", "Share"
                ]
            }
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def img_to_b64(file):
    if file: return base64.b64encode(file.getvalue()).decode()
    return None

db = load_data()

# --- 2. Page Config ---
st.set_page_config(page_title="NMS ERP System", layout="wide")
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# --- 3. Login Logic ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP System - Login")
    c1, c2 = st.columns(2)
    with c1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=220)
        logo_up = st.file_uploader("Upload Company Logo", type=['png', 'jpg'])
        if st.button("Save Logo"):
            db["logo"] = img_to_b64(logo_up); save_data(db); st.rerun()
    with c2:
        u_choice = st.selectbox("Employee Login", list(db["users"].keys()))
        p_input = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if db["users"][u_choice]["pass"] == p_input:
                st.session_state.update({'logged_in': True, 'user': u_choice, 'role': db["users"][u_choice]["role"]})
                st.rerun()
            else: st.error("Access Denied: Wrong Password")
else:
    # --- 4. Sidebar (Admin & Profile) ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"Welcome, {st.session_state['user']}")
        user_info = db["users"][st.session_state['user']]
        if user_info.get("photo"): st.image(base64.b64decode(user_info["photo"]), width=150)
        p_up = st.file_uploader("Upload Profile Photo", type=['png', 'jpg'])
        if st.button("Save My Photo"):
            db["users"][st.session_state['user']]["photo"] = img_to_b64(p_up); save_data(db); st.rerun()
        
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ Manager Options")
            target = st.selectbox("Edit Employee Data", list(db["users"].keys()))
            db["users"][target]["full_name"] = st.text_input("Full Name", db["users"][target].get("full_name", ""))
            db["users"][target]["email"] = st.text_input("Email Address", db["users"][target].get("email", ""))
            db["users"][target]["phone"] = st.text_input("Mobile Number", db["users"][target].get("phone", ""))
            db["users"][target]["address"] = st.text_input("Residential Address", db["users"][target].get("address", ""))
            db["users"][target]["id_num"] = st.text_input("National ID", db["users"][target].get("id_num", ""))
            db["users"][target]["pass"] = st.text_input("Login Password", db["users"][target].get("pass", ""))
            if st.button("Update Employee Info"): save_data(db); st.success("Employee Data Saved!")

    # --- 5. Main Application ---
    st.title("📋 Daily Operational Report")
    
    # Auto Shift Info
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.write("**Date:**"); st.info(datetime.now().strftime('%Y-%m-%d'))
    with inf2: st.write("**Day:**"); st.info(datetime.now().strftime('%A'))
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift_time = st.selectbox("Shift Time", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: START", "🔴 TAB 2: END", "📱 TAB 3: MARKETING"])

    with tab1:
        st.subheader("Shift Start Requirements")
        c_chk, c_cash, c_pr = st.columns([1, 1.5, 1.5])
        with c_chk:
            for t in db["tasks"]["start"]: st.checkbox(t, key=f"s_{t}")
        with c_cash:
            st.write("**Opening Cash (Denominations)**")
            total_open = 0
            for d in [200, 100, 50, 20, 10, 5]:
                val = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}")
                total_open += (val * d)
            o_coins = st.number_input("Opening Coins", step=1, key="o_coins")
            total_open += o_coins
            st.success(f"**Total Opening Cash: {total_open} LE**")
        with c_pr:
            st.write("**Printers Opening Counters**")
            k_start = st.number_input("Kyocera Opening Counter", step=1)
            x_start = st.number_input("Xerox Opening Counter", step=1)
            st.divider()
            opay_start = st.number_input("Opay Opening Balance", step=1)

    with tab2:
        st.subheader("Shift End Requirements")
        c_chk2, c_cash2, c_pr2 = st.columns([1, 1.5, 1.5])
        with c_chk2:
            for t in db["tasks"]["end"]: st.checkbox(t, key=f"e_{t}")
            st.divider()
            st.write("**Non-Cash Transactions**")
            instapay = st.number_input("Instapay", step=1)
            wallet = st.number_input("Wallet (Vodafone...)", step=1)
            visa = st.number_input("Visa / Card", step=1)
        with c_cash2:
            st.write("**Closing Cash (Denominations)**")
            total_close = 0
            for d in [200, 100, 50, 20, 10, 5]:
                val = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}")
                total_close += (val * d)
            c_coins = st.number_input("Closing Coins", step=1, key="c_coins")
            total_close += c_coins
            expenses = st.number_input("Total Expenses", step=1)
            net_cash_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Balance", f"{net_diff} LE" if 'net_diff' in locals() else f"{net_cash_diff} LE")
        with c_pr2:
            st.write("**Printer Usage Reconciliation**")
            # Kyocera
            st.markdown("--- *Kyocera Machine* ---")
            k_end = st.number_input("Kyocera Final Counter", step=1)
            k_os = st.number_input("Kyo One-Side Count", step=1)
            k_dup = st.number_input("Kyo Duplex (Calculates as 2)", step=1)
            k_draft = st.number_input("Kyo Draft/Errors", step=1)
            k_real_usage = k_end - k_start
            k_manual_total = k_os + (k_dup * 2) + k_draft
            st.warning(f"Kyo Diff: {k_manual_total - k_real_usage}")
            
            # Xerox
            st.markdown("--- *Xerox Machine* ---")
            x_end = st.number_input("Xerox Final Counter", step=1)
            x_os = st.number_input("Xerox One-Side Count", step=1)
            x_dup = st.number_input("Xerox Duplex (Calculates as 2)", step=1)
            x_draft = st.number_input("Xerox Draft/Errors", step=1)
            x_real_usage = x_end - x_start
            x_manual_total = x_os + (x_dup * 2) + x_draft
            st.warning(f"Xerox Diff: {x_manual_total - x_real_usage}")
            
            st.divider()
            opay_end = st.number_input("Opay Final Balance", step=1)
            opay_diff = opay_end - opay_start

    with tab3:
        st.subheader("Social Media & Marketing Checklist")
        m_cols = st.columns(4)
        m_results = {}
        for i, task in enumerate(db["tasks"]["marketing"]):
            m_results[task] = m_cols[i % 4].checkbox(task, key=f"m_{task}")

    # --- 6. Final Reporting ---
    st.divider()
    btn_pdf, btn_wa = st.columns(2)
    
    report_text = f"""*🚀 NMS DAILY REPORT*
📅 *Date:* {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A')})
📍 *Branch:* {branch}
👤 *Employee:* {st.session_state['user']}
🕒 *Shift:* {shift_time}

*💰 FINANCIALS:*
- Cash Diff: {net_cash_diff} LE
- Expenses: {expenses} LE
- Non-Cash (Total): {instapay + wallet + visa} LE
- Opay Diff: {opay_diff} LE

*🖨️ PRINTERS (Actual vs Counters):*
- Kyocera Usage: {k_manual_total}
- Xerox Usage: {x_manual_total}

*📱 MARKETING:*
- Tasks Completed: {sum(m_results.values())}/{len(m_results)}"""

    with btn_pdf:
        if st.button("📥 Generate Full PDF Report", use_container_width=True):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"NMS SYSTEM REPORT", styles['Title']))
            elements.append(Paragraph(f"Branch: {branch} | Employee: {st.session_state['user']}", styles['Normal']))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A')})", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            tbl_data = [
                ["Category", "Detail", "Value"],
                ["Cash", "Opening Balance", f"{total_open} LE"],
                ["Cash", "Closing Balance", f"{total_close} LE"],
                ["Cash", "Net Difference", f"{net_cash_diff} LE"],
                ["Printers", "Kyocera Usage", f"{k_manual_total}"],
                ["Printers", "Xerox Usage", f"{x_manual_total}"],
                ["Opay", "Difference", f"{opay_diff} LE"],
                ["Non-Cash", "Total", f"{instapay+wallet+visa} LE"]
            ]
            t = Table(tbl_data, colWidths=[120, 220, 100])
            t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
            elements.append(t)
            doc.build(elements)
            st.download_button("Download PDF", data=buffer.getvalue(), file_name=f"Report_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf")

    with btn_wa:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(report_text)}"
        st.markdown(f'''
            <a href="{wa_url}" target="_blank">
                <button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold;">
                    📱 Send Report to Manager WhatsApp
                </button>
            </a>
        ''', unsafe_allow_html=True)
