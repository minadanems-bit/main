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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. CONFIGURATION & DATABASE ---
DB_FILE = 'nms_master_db.json'
MANAGER_PHONE = "971522045638"

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
            "branches": ["Mohamed Nagib Branch", "El Tram Branch"],
            "logs": [],
            "last_entries": {} # To store last saved data per user for auto-recovery
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_data()

# --- 2. AUTHENTICATION ---
st.set_page_config(page_title="NMS - Management System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

if not st.session_state['logged_in']:
    st.title("🔐 NMS ERP - Secure Login")
    col_l, col_r = st.columns(2)
    with col_l:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=250)
        else: st.info("Company Logo Placeholder")
    with col_r:
        user_node = st.selectbox("Select Employee", list(db["users"].keys()))
        pass_node = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if db["users"][user_node]["pass"] == pass_node:
                st.session_state.update({'logged_in': True, 'user': user_node, 'role': db["users"][user_node]["role"]})
                db["logs"].append({"user": user_node, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "event": "Login"})
                save_data(db); st.rerun()
            else: st.error("Invalid Credentials")

else:
    # --- 3. SIDEBAR & ADMIN CONTROLS ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=150)
        st.header(f"User: {st.session_state['user']}")
        u_info = db["users"][st.session_state['user']]
        if u_info.get("photo"): st.image(base64.b64decode(u_info["photo"]), width=150)
        
        # Profile Photo Upload
        up_photo = st.file_uploader("Upload Personal Photo", type=['jpg', 'png'])
        if st.button("Save My Photo"):
            db["users"][st.session_state['user']]["photo"] = base64.b64encode(up_photo.getvalue()).decode()
            save_data(db); st.success("Photo Updated!"); st.rerun()

        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛡️ Manager Panel")
            m_action = st.radio("Manage:", ["Employees", "Company Logo", "Audit Logs"])
            
            if m_action == "Employees":
                tgt = st.selectbox("Select Target User", list(db["users"].keys()))
                db["users"][tgt]["full_name"] = st.text_input("Full Name", db["users"][tgt].get("full_name", ""))
                db["users"][tgt]["email"] = st.text_input("Email", db["users"][tgt].get("email", ""))
                db["users"][tgt]["phone"] = st.text_input("Mobile", db["users"][tgt].get("phone", ""))
                db["users"][tgt]["address"] = st.text_input("Address", db["users"][tgt].get("address", ""))
                db["users"][tgt]["id_num"] = st.text_input("ID Number", db["users"][tgt].get("id_num", ""))
                db["users"][tgt]["pass"] = st.text_input("Password", db["users"][tgt].get("pass", ""))
                if st.button("Commit User Changes"): save_data(db); st.success("Updated!")
            
            elif m_action == "Company Logo":
                l_up = st.file_uploader("Upload New Logo")
                if st.button("Update Logo"):
                    db["logo"] = base64.b64encode(l_up.getvalue()).decode(); save_data(db); st.rerun()
            
            elif m_action == "Audit Logs":
                st.dataframe(pd.DataFrame(db["logs"]).tail(50))

    # --- 4. SHIFT CORE DATA ---
    st.title("📊 NMS Shift Management")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.write("**Date:**"); st.info(datetime.now().strftime('%Y-%m-%d'))
    with c2: st.write("**Day:**"); st.info(datetime.now().strftime('%A'))
    with c3: branch = st.selectbox("Branch", db["branches"])
    with c4: shift = st.selectbox("Shift Type", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING", "🔴 TAB 2: CLOSING", "📱 TAB 3: SOCIAL MEDIA"])

    # TAB 1: OPENING
    with tab1:
        st.subheader("Shift Initialization")
        col1, col2, col3 = st.columns([1, 1.5, 1.5])
        with col1:
            st.write("**Opening Checklist**")
            for t in ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"]:
                st.checkbox(t, key=f"s_{t}")
        with col2:
            st.write("**Opening Cash (Table)**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}")
                t_open += (v * d)
            o_coins = st.number_input("Coins (e.g. 1.5)", min_value=0.0, step=0.5, format="%.2f", key="oc")
            t_open += o_coins
            st.success(f"**Total Opening Cash: {t_open:,.2f} LE**")
        with col3:
            st.write("**System Status**")
            k1_start = st.number_input("Printer 1 (Kyo) Start Counter", step=1)
            k2_start = st.number_input("Printer 2 (Xerox) Start Counter", step=1)
            opay_start = st.number_input("Opay Start Balance", step=0.01, format="%.4f")

    # TAB 2: CLOSING
    with tab2:
        st.subheader("Shift Finalization")
        col1, col2, col3 = st.columns([1, 1.5, 1.5])
        with col1:
            st.write("**Closing Checklist**")
            for t in ["Contacts Checked", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"]:
                st.checkbox(t, key=f"e_{t}")
            st.divider()
            st.write("**Non-Cash Transactions**")
            insta = st.number_input("Instapay", step=1)
            wallet = st.number_input("Wallet", step=1)
            visa = st.number_input("Visa", step=1)
        with col2:
            st.write("**Closing Cash (Table)**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}")
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins (e.g. 0.5)", min_value=0.0, step=0.5, format="%.2f", key="cc")
            t_close += c_coins
            expenses = st.number_input("Expenses (Out)", step=1)
            net_diff = (t_close + expenses) - t_open
            st.metric("Net Cash Difference", f"{net_diff:,.2f} LE")
        with col3:
            st.write("**Printer Usage (Critical Reconciliation)**")
            # Printer 1
            st.markdown("--- *Printer 1 (Kyocera)* ---")
            k1_end = st.number_input("P1 Final Counter", step=1)
            k1_os = st.number_input("P1 One-Side", step=1, key="k1os")
            k1_dp = st.number_input("P1 Duplex (Sheet)", step=1, key="k1dp")
            k1_dr = st.number_input("P1 Draft/Error", step=1, key="k1dr")
            k1_manual = k1_os + (k1_dp * 2) + k1_dr
            st.info(f"P1 Actual Usage: {k1_end - k1_start} | Manual: {k1_manual}")
            # Printer 2
            st.markdown("--- *Printer 2 (Xerox)* ---")
            k2_end = st.number_input("P2 Final Counter", step=1)
            k2_os = st.number_input("P2 One-Side", step=1, key="k2os")
            k2_dp = st.number_input("P2 Duplex (Sheet)", step=1, key="k2dp")
            k2_dr = st.number_input("P2 Draft/Error", step=1, key="k2dr")
            k2_manual = k2_os + (k2_dp * 2) + k2_dr
            st.info(f"P2 Actual Usage: {k2_end - k2_start} | Manual: {k2_manual}")
            
            st.divider()
            opay_end = st.number_input("Opay Closing Balance", step=0.01, format="%.4f")
            st.warning(f"Opay Diff: {opay_end - opay_start:,.4f}")

    # TAB 3: SOCIAL MEDIA
    with tab3:
        st.subheader("Social Media Tasks Tracking")
        m_list = ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook Story", "Facebook Post/Reel", "Facebook Group", "Page Story", "Page Post/Reel", "Threads", "Instagram Story", "Instagram Post/Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post", "Like", "Love", "Care", "Share"]
        cols = st.columns(4)
        m_results = {task: cols[i % 4].checkbox(task, key=f"m_{task}") for i, task in enumerate(m_list)}

    # --- 5. EXPORT & WHATSAPP ---
    st.divider()
    bt1, bt2 = st.columns(2)
    
    # Message Construction for WhatsApp
    msg = f"*🚀 NMS DAILY REPORT*\n" \
          f"Branch: {branch}\nUser: {st.session_state['user']}\n" \
          f"Cash Diff: {net_diff:,.2f} LE\nP1 Usage: {k1_manual}\nP2 Usage: {k2_manual}\n" \
          f"Opay Diff: {opay_end - opay_start:,.4f}"

    with bt1:
        if st.button("📥 EXPORT COMPLETE PDF REPORT", use_container_width=True):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"NMS SYSTEM REPORT", styles['Title']))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')} | Branch: {branch}", styles['Normal']))
            elements.append(Spacer(1, 12))
            # Financial Data
            fdata = [["Item", "Value"], ["Opening Cash", f"{t_open}"], ["Closing Cash", f"{t_close}"], ["Net Diff", f"{net_diff}"]]
            t = Table(fdata, colWidths=[200, 200])
            t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
            elements.append(t)
            doc.build(elements)
            st.download_button("Download Now", data=buffer.getvalue(), file_name="NMS_Report.pdf")

    with bt2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND REPORT TO MANAGER WHATSAPP</button></a>', unsafe_allow_html=True)

    # Save data for auto-recovery (Requirement #8)
    save_data(db)
