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

# --- 1. Database Engine ---
DB_FILE = 'nms_enterprise_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "HQ", "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None}
            },
            "branches": ["Mohamed Nagib Branch", "El Tram Branch"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [],
            "drafts": {}
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & Session Logic ---
st.set_page_config(page_title="NMS Management System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # الحفظ التلقائي لكل المدخلات البرمجية
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_'))}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# --- 3. Login System ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Enterprise Login")
    col1, col2 = st.columns([1, 1])
    with col1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=250)
    with col2:
        u = st.selectbox("Select Employee", list(db["users"].keys()))
        p = st.text_input("Password", type="password")
        if st.button("Login to System", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items():
                        st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Authentication Failed")

else:
    # --- 4. Sidebar ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"User: {st.session_state['user']}")
        user_node = db["users"][st.session_state['user']]
        if user_node.get("photo"): st.image(base64.b64decode(user_node["photo"]), width=150)
        
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Master Control")
            admin_mode = st.radio("Settings", ["Manage Employees", "Manage Branches", "Manage Tasks", "Audit Logs"])
            # (نفس كود الإدارة السابق...)
            if admin_mode == "Manage Employees":
                st.subheader("👥 Employee Master Control")
                with st.expander("➕ Register New Employee"):
                    new_u_name = st.text_input("Username")
                    new_u_pass = st.text_input("Password", type="password")
                    if st.button("Create Account"):
                        db["users"][new_u_name] = {"pass": new_u_pass, "role": "user", "full_name": new_u_name}
                        save_db(db); st.success("Created!"); st.rerun()

    # --- 5. Main Dashboard ---
    st.title("📊 Daily Shift Control")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with inf2: st.info(f"🕒 **Day:** {datetime.now().strftime('%A')}")
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING", "🔴 TAB 2: CLOSING", "📱 TAB 3: SOCIAL MEDIA"])

    with tab1:
        st.subheader("Opening Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Opening Checklist**")
            for t in db["tasks"]["opening"]: 
                st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, format="%.2f", key="oc", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total Opening: {t_open:,.2f} LE**")
        with c3:
            st.write("**Start Counters**")
            k_start = st.number_input("Kyocera Start", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            opay_start = st.number_input("Opay Start Balance", step=0.01, format="%.4f", key="ops", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: 
                st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.write("**Financial (System)**")
            sys_sales = st.number_input("System Sales (SQL)", min_value=0.0, step=1.0, key="c_sys_sales", on_change=sync_draft)
            instapay = st.number_input("Instapay", step=1, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1, key="c_visa", on_change=sync_draft)
        with c2:
            st.write("**Closing Cash (Physical)**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            expenses = st.number_input("Expenses", step=1, key="c_exp", on_change=sync_draft)
            
            st.divider()
            expected_cash = t_open + sys_sales - expenses
            net_diff = t_close - expected_cash
            
            st.metric("Expected Cash", f"{expected_cash:,.2f} LE")
            if net_diff == 0: st.success("✅ Match")
            elif net_diff > 0: st.warning(f"➕ Surplus: {net_diff:,.2f}")
            else: st.error(f"➖ Shortage: {net_diff:,.2f}")

        with c3:
            st.write("**Printer Analysis**")
            k_end = st.number_input("Kyo Final", step=1, key="k1end", on_change=sync_draft)
            k_os = st.number_input("Kyo One-Side", step=1, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("Kyo Duplex", step=1, key="k1dp", on_change=sync_draft)
            k_actual = k_end - k_start
            k_manual = k_os + (k_dp * 2)
            
            x_end = st.number_input("Xerox Final", step=1, key="x2end", on_change=sync_draft)
            x_os = st.number_input("Xerox One-Side", step=1, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("Xerox Duplex", step=1, key="x2dp", on_change=sync_draft)
            x_actual = x_end - x_start
            x_manual = x_os + (x_dp * 2)
            opay_end = st.number_input("Opay Final", step=0.01, format="%.4f", key="op_end", on_change=sync_draft)

    with tab3:
        st.subheader("Social Media Tasks")
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["social"]):
            m_cols[i%4].checkbox(task, key=f"m_{task}", on_change=sync_draft)

    # --- 6. Professional Exporting ---
    st.divider()
    opening_tasks_done = [t for t in db["tasks"]["opening"] if st.session_state.get(f"s_{t}")]
    closing_tasks_done = [t for t in db["tasks"]["closing"] if st.session_state.get(f"e_{t}")]
    
    diff_status = "✅ Match" if net_diff == 0 else f"➕ Surplus: {net_diff}" if net_diff > 0 else f"➖ Shortage: {net_diff}"
    wa_msg = f"*🚀 NMS FULL REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n*💰 FINANCIAL:*\n- System Sales: {sys_sales:,.2f}\n- Expenses: {expenses:,.2f}\n- *Cash Status:* {diff_status}\n\n*🖨️ PRINTERS:*\n- Kyo Actual: {k_actual}\n- Xerox Actual: {x_actual}\n\n*✅ TASKS:*\n- Opening: {len(opening_tasks_done)}/{len(db['tasks']['opening'])}\n- Closing: {len(closing_tasks_done)}/{len(db['tasks']['closing'])}"

    c_rep1, c_rep2 = st.columns(2)
    with c_rep1:
        if st.button("📥 DOWNLOAD PDF REPORT", use_container_width=True):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = [Paragraph(f"NMS REPORT - {branch}", styles['Title']), Spacer(1, 12)]
            
            # Financial Table
            data_fin = [["Category", "Details"], ["Opening", t_open], ["System Sales", sys_sales], ["Expenses", expenses], ["Actual Cash", t_close], ["Difference", net_diff]]
            elements.append(Table(data_fin, style=TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.grey)])))
            
            doc.build(elements)
            st.download_button("Save PDF", data=buffer.getvalue(), file_name="NMS_Report.pdf")

    with c_rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold;">📱 SEND TO WHATSAPP</button></a>', unsafe_allow_html=True)
