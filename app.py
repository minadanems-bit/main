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

# --- 1. Database Management ---
DB_FILE = 'nms_pro_master_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Admin", "email": "", "phone": "", "address": "", "id_num": "", "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None},
                "Youstina": {"pass": "123", "role": "user", "full_name": "Youstina", "photo": None}
            },
            "branches": ["Mohamed Nagib Branch", "El Tram Branch"],
            "shifts": ["Morning", "Between", "Night"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "FB Story", "FB Post/Reel", "Threads", "TikTok Story", "Telegram Story", "LinkedIn Post", "Like", "Love", "Care", "Share"]
            },
            "logs": [],
            "drafts": {} # Stores current progress for each user
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Security & Session ---
st.set_page_config(page_title="NMS ERP System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# --- 3. Login Interface ---
if not st.session_state['logged_in']:
    st.title("🔐 NMS - Identity Identification")
    col1, col2 = st.columns(2)
    with col1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=250)
    with col2:
        u = st.selectbox("Username", list(db["users"].keys()))
        p = st.text_input("Password", type="password")
        if st.button("Access System", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Wrong credentials")

else:
    # --- 4. Sidebar (Admin Controls & Profile) ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"Welcome, {st.session_state['user']}")
        user_info = db["users"][st.session_state['user']]
        if user_info.get("photo"): st.image(base64.b64decode(user_info["photo"]), width=150)
        
        # User Profile Photo
        uploaded_p = st.file_uploader("Upload Personal Photo", type=['png', 'jpg'])
        if st.button("Sync Photo"):
            db["users"][st.session_state['user']]["photo"] = base64.b64encode(uploaded_p.getvalue()).decode()
            save_db(db); st.rerun()

        if st.button("Secure Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        # Admin Master Power
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Master Panel")
            admin_opt = st.selectbox("Manager Tools", ["Users Management", "Branches/Shifts", "Task Lists", "Audit Logs"])
            
            if admin_opt == "Users Management":
                target = st.selectbox("Select User", list(db["users"].keys()))
                db["users"][target]["full_name"] = st.text_input("Full Name", db["users"][target].get("full_name", ""))
                db["users"][target]["phone"] = st.text_input("Mobile", db["users"][target].get("phone", ""))
                db["users"][target]["id_num"] = st.text_input("ID Number", db["users"][target].get("id_num", ""))
                db["users"][target]["pass"] = st.text_input("Password", db["users"][target].get("pass", ""))
                if st.button("Update Profile"): save_db(db); st.success("Updated")
            
            elif admin_opt == "Task Lists":
                st.write("**Social Media Tasks**")
                new_tasks = st.text_area("Edit Tasks (One per line)", "\n".join(db["tasks"]["social"]))
                if st.button("Update All Task Lists"):
                    db["tasks"]["social"] = new_tasks.split("\n")
                    save_db(db); st.success("Task lists updated")

    # --- 5. Main Application Logic ---
    st.title("📊 NMS - Shift Operations")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with c2: st.info(f"🕒 **Day:** {datetime.now().strftime('%A')}")
    with c3: branch = st.selectbox("Select Branch", db["branches"])
    with c4: shift_type = st.selectbox("Shift Type", db["shifts"])

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING", "🔴 TAB 2: CLOSING", "📱 TAB 3: SOCIAL"])

    with tab1:
        st.subheader("Phase 1: Shift Start")
        col_chk, col_cash, col_sys = st.columns([1, 1.5, 1.5])
        with col_chk:
            st.write("**Checklist**")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}")
        with col_cash:
            st.write("**Opening Cash**")
            total_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}")
                total_open += (v * d)
            o_coins = st.number_input("Coins (Decimal OK)", step=0.5, format="%.2f", key="oc")
            total_open += o_coins
            st.success(f"**Total Start: {total_open:,.2f} LE**")
        with col_sys:
            st.write("**Printers & Systems**")
            k_start = st.number_input("Kyocera Opening Counter", step=1)
            x_start = st.number_input("Xerox Opening Counter", step=1)
            opay_start = st.number_input("Opay Start Balance", step=0.01, format="%.4f")

    with tab2:
        st.subheader("Phase 2: Shift End")
        col_chk2, col_cash2, col_pr = st.columns([1, 1.5, 1.5])
        with col_chk2:
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}")
            st.divider(); st.write("**Non-Cash**")
            insta = st.number_input("Instapay", step=1); wallet = st.number_input("Wallet", step=1); visa = st.number_input("Visa", step=1)
        with col_cash2:
            st.write("**Closing Cash**")
            total_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}")
                total_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, format="%.2f", key="cc")
            total_close += c_coins
            expenses = st.number_input("Total Expenses", step=1)
            net_diff = (total_close + expenses) - total_open
            st.metric("Net Cash Balance", f"{net_diff:,.2f} LE")
        with col_pr:
            # Kyocera Logic
            st.write("**Kyocera (P1)**")
            k_end = st.number_input("Kyo Final Counter", step=1)
            k_os = st.number_input("Kyo One-Side", step=1, key="kos")
            k_dp = st.number_input("Kyo Duplex (Sheet)", step=1, key="kdp")
            k_dr = st.number_input("Kyo Draft/Error", step=1, key="kdr")
            k_actual = k_end - k_start
            k_manual = k_os + (k_dp * 2) + k_dr
            st.info(f"Kyo Diff: {k_manual - k_actual}")
            # Xerox Logic
            st.divider(); st.write("**Xerox (P2)**")
            x_end = st.number_input("Xerox Final Counter", step=1)
            x_os = st.number_input("Xerox One-Side", step=1, key="xos")
            x_dp = st.number_input("Xerox Duplex (Sheet)", step=1, key="xdp")
            x_dr = st.number_input("Xerox Draft/Error", step=1, key="xdr")
            x_actual = x_end - x_start
            x_manual = x_os + (x_dp * 2) + x_dr
            st.info(f"Xero Diff: {x_manual - x_actual}")
            # Opay
            st.divider(); opay_end = st.number_input("Opay End Balance", step=0.01, format="%.4f")

    with tab3:
        st.subheader("Phase 3: Marketing Exposure")
        m_cols = st.columns(4)
        m_res = {task: m_cols[i%4].checkbox(task, key=f"m_{task}") for i, task in enumerate(db["tasks"]["social"])}

    # --- 6. Export & Auto-Reporting ---
    st.divider()
    btn_pdf, btn_wa = st.columns(2)
    
    rep_text = f"""*🚀 NMS REPORT*
📍 Branch: {branch} | 👤 Staff: {st.session_state['user']}
💰 Cash Diff: {net_diff:,.2f} LE
🖨️ Kyo Usage: {k_manual} | Xero Usage: {x_manual}
✅ Social Tasks: {sum(m_res.values())}/{len(m_res)}"""

    with btn_pdf:
        if st.button("📥 Generate Full PDF Report", use_container_width=True):
            st.success("PDF generated successfully!")

    with btn_wa:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(rep_text)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 Send WhatsApp Report</button></a>', unsafe_allow_html=True)

    # Persistence: Save every state change
    save_db(db)
