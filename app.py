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

# --- 1. Settings & Persistence Logic ---
DB_FILE = 'nms_pro_database.json'
MANAGER_PHONE = "971522045638"

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "General Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "Dubai", "photo": None},
                "Mina": {"pass": "1234", "role": "user", "full_name": "Mina", "photo": None},
                "Youstina": {"pass": "1234", "role": "user", "full_name": "Youstina", "photo": None},
                "Mark": {"pass": "1234", "role": "user", "full_name": "Mark", "photo": None},
                "Fatma": {"pass": "1234", "role": "user", "full_name": "Fatma", "photo": None}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "logs": [],
            "drafts": {} # To save progress for each user
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def img_to_b64(file):
    if file: return base64.b64encode(file.getvalue()).decode()
    return None

db = load_data()

# --- 2. Page Setup ---
st.set_page_config(page_title="NMS Pro ERP", layout="wide")
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# --- 3. Login Logic ---
if not st.session_state['logged_in']:
    st.title("🛡️ NMS ERP Pro - Security Portal")
    c1, c2 = st.columns(2)
    with c1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=200)
        logo_up = st.file_uploader("Company Identity (Logo)", type=['png', 'jpg'])
        if st.button("Save Identity"):
            db["logo"] = img_to_b64(logo_up); save_data(db); st.rerun()
    with c2:
        u_choice = st.selectbox("Identity Identification", list(db["users"].keys()))
        p_input = st.text_input("Access Token (Password)", type="password")
        if st.button("Authorize Access", use_container_width=True):
            if db["users"][u_choice]["pass"] == p_input:
                st.session_state.update({'logged_in': True, 'user': u_choice, 'role': db["users"][u_choice]["role"]})
                db["logs"].append({"user": u_choice, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_data(db); st.rerun()
            else: st.error("Invalid Credentials")
else:
    # Initialize draft if not exists
    if st.session_state['user'] not in db["drafts"]:
        db["drafts"][st.session_state['user']] = {}

    # --- 4. Sidebar ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"Account: {st.session_state['user']}")
        user_info = db["users"][st.session_state['user']]
        if user_info.get("photo"): st.image(base64.b64decode(user_info["photo"]), width=150)
        p_up = st.file_uploader("Update Profile Photo", type=['png', 'jpg'])
        if st.button("Sync Photo"):
            db["users"][st.session_state['user']]["photo"] = img_to_b64(p_up); save_data(db); st.rerun()
        
        if st.button("Secure Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Controls")
            admin_mode = st.radio("Management", ["Employees Records", "Access Logs"])
            
            if admin_mode == "Employees Records":
                target = st.selectbox("Target Employee", list(db["users"].keys()))
                db["users"][target]["full_name"] = st.text_input("Full Name", db["users"][target].get("full_name", ""))
                db["users"][target]["phone"] = st.text_input("Mobile", db["users"][target].get("phone", ""))
                db["users"][target]["address"] = st.text_input("Address", db["users"][target].get("address", ""))
                db["users"][target]["id_num"] = st.text_input("ID Card No.", db["users"][target].get("id_num", ""))
                db["users"][target]["pass"] = st.text_input("Password", db["users"][target].get("pass", ""))
                if st.button("Commit Changes"): save_data(db); st.success("Employee Profile Updated")
                if st.button("Delete User Account", type="primary"):
                    if target != "admin": del db["users"][target]; save_data(db); st.rerun()
            else:
                st.write("**System History Log**")
                st.dataframe(pd.DataFrame(db["logs"]).tail(20), use_container_width=True)

    # --- 5. Report Body ---
    st.title("📊 Daily Shift Performance")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.write("**Date:**"); st.info(datetime.now().strftime('%Y-%m-%d'))
    with inf2: st.write("**Day:**"); st.info(datetime.now().strftime('%A'))
    with inf3: branch = st.selectbox("Branch Selection", db["branches"])
    with inf4: shift_time = st.selectbox("Shift Type", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 PHASE 1: START", "🔴 PHASE 2: END", "📱 PHASE 3: SOCIAL"])

    with tab1:
        st.subheader("Shift Initialization")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Checklist**")
            s_tasks = ["Finger print", "Power on", "Uniform and name tag", "Music on", "Paper loaded", "Cash counted", "All good"]
            for t in s_tasks: st.checkbox(t, key=f"s_{t}")
        with c2:
            st.write("**Opening Liquidity**")
            total_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}")
                total_open += (v * d)
            o_coins = st.number_input("Coins (Decimal OK)", step=0.5, format="%.2f", key="o_coins")
            total_open += o_coins
            st.success(f"**Total Opening: {total_open:,.2f} LE**")
        with c3:
            st.write("**Systems Initial State**")
            k_start = st.number_input("Kyo Start Counter", step=1, key="k_start")
            x_start = st.number_input("Xerox Start Counter", step=1, key="x_start")
            opay_start = st.number_input("Opay Start (Decimal OK)", step=0.01, format="%.4f", key="op_start")

    with tab2:
        st.subheader("Shift Finalization")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Closing Checklist**")
            e_tasks = ["Contacts", "Place cleaned", "Power off", "Cash counted", "Finger print", "Report sent"]
            for t in e_tasks: st.checkbox(t, key=f"e_{t}")
            st.divider()
            st.write("**Digital Revenue**")
            insta = st.number_input("Instapay", step=1)
            wallet = st.number_input("Wallet", step=1)
            visa = st.number_input("Visa", step=1)
        with c2:
            st.write("**Closing Liquidity**")
            total_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}")
                total_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, format="%.2f", key="c_coins")
            total_close += c_coins
            expenses = st.number_input("Shift Expenses", step=1)
            net_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Reconciliation", f"{net_diff:,.2f} LE")
        with c3:
            st.write("**Printer Reconciliation (Duplex=2)**")
            k_end = st.number_input("Kyo Final Counter", step=1)
            k_os = st.number_input("Kyo One-Side", step=1, key="kos")
            k_dup = st.number_input("Kyo Duplex (Sheet)", step=1, key="kdup")
            k_dr = st.number_input("Kyo Draft/Error", step=1)
            k_calc = k_os + (k_dup * 2) + k_dr
            k_actual = k_end - k_start
            st.warning(f"Kyo Diff: {k_calc - k_actual}")
            
            st.markdown("---")
            x_end = st.number_input("Xerox Final Counter", step=1)
            x_os = st.number_input("Xerox One-Side", step=1, key="xos")
            x_dup = st.number_input("Xerox Duplex (Sheet)", step=1, key="xdup")
            x_dr = st.number_input("Xerox Draft/Error", step=1)
            x_calc = x_os + (x_dup * 2) + x_dr
            x_actual = x_end - x_start
            st.warning(f"Xerox Diff: {x_calc - x_actual}")
            
            st.divider()
            opay_end = st.number_input("Opay Final (Decimal OK)", step=0.01, format="%.4f")
            st.info(f"Opay Diff: {opay_end - opay_start:,.4f}")

    with tab3:
        st.subheader("Marketing & Exposure Tasks")
        m_list = ["Canva 1", "Canva 2", "WhatsApp story", "WhatsApp channel", "FB story", "FB post/reel", "FB group", "Page story", "Page post/reel", "Threads", "Instagram story", "Instagram post/reel", "TikTok story", "TikTok post", "Telegram story", "Telegram channel", "LinkedIn post", "Like", "Love", "Care", "Share"]
        m_cols = st.columns(4)
        m_res = {task: m_cols[i%4].checkbox(task, key=f"m_{task}") for i, task in enumerate(m_list)}

    # --- 6. Export Actions ---
    st.divider()
    b1, b2 = st.columns(2)
    
    wa_msg = f"*🚀 NMS SHIFT REPORT*\n" \
             f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n" \
             f"📍 Branch: {branch}\n" \
             f"👤 User: {st.session_state['user']}\n" \
             f"💰 Cash Diff: {net_diff:,.2f} LE\n" \
             f"🖨️ Kyo Usage: {k_calc}\n" \
             f"🖨️ Xerox Usage: {x_calc}\n" \
             f"💳 Opay Diff: {opay_end - opay_start:,.4f}\n" \
             f"✅ Marketing: {sum(m_res.values())}/{len(m_res)}"

    with b1:
        if st.button("📥 EXPORT PDF (Full Tables)", use_container_width=True):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"NMS SYSTEM REPORT - {branch}", styles['Title']))
            elements.append(Paragraph(f"User: {st.session_state['user']} | Shift: {shift_time}", styles['Normal']))
            data = [["Section", "Details", "Metric"], ["Financial", "Cash Diff", f"{net_diff:,.2f}"], ["Printer", "Kyo Total", f"{k_calc}"], ["Printer", "Xerox Total", f"{x_calc}"], ["Digital", "Opay Diff", f"{opay_end-opay_start:,.4f}"]]
            t = Table(data, colWidths=[100, 200, 100])
            t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
            elements.append(t); doc.build(elements)
            st.download_button("Download Now", data=buffer.getvalue(), file_name=f"Report_{datetime.now().strftime('%y%m%d')}.pdf")

    with b2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold;">📱 SEND TO MANAGER WHATSAPP</button></a>', unsafe_allow_html=True)

    # Save Draft on every interaction (Simulated by save_data at the end)
    save_data(db)
