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
            "logo": None, "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "HQ", "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None}
            },
            "branches": ["M. Nagib Branch", "Tram Branch"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [], "drafts": {}
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
                    for key, val in db["drafts"][u].items(): st.session_state[key] = val
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
        prof_pic = st.file_uploader("Upload Personal Photo", type=['jpg', 'png'])
        if st.button("Save Photo"):
            if prof_pic:
                db["users"][st.session_state['user']]["photo"] = base64.b64encode(prof_pic.getvalue()).decode()
                save_db(db); st.success("Photo Updated!"); st.rerun()
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        if st.session_state['role'] == 'admin':
            st.divider(); st.subheader("🛠️ Admin Master Control")
            admin_mode = st.radio("Settings", ["Manage Employees", "Manage Branches", "Manage Tasks", "Audit Logs"])
            if admin_mode == "Manage Employees":
                st.subheader("👥 Employee Master Control")
                with st.expander("➕ Register"):
                    new_u = st.text_input("Username")
                    new_p = st.text_input("Password", type="password")
                    if st.button("Create"):
                        db["users"][new_u] = {"pass": new_p, "role": "user", "full_name": new_u}
                        save_db(db); st.rerun()
                target_user = st.selectbox("Select Employee", list(db["users"].keys()))
                db["users"][target_user]["full_name"] = st.text_input("Full Name", db["users"][target_user].get("full_name", ""))
                db["users"][target_user]["pass"] = st.text_input("Password", db["users"][target_user]["pass"])
                if st.button("💾 Save Changes"): save_db(db); st.success("Updated!")

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
        if db.get("pending_debit", 0) > 0: st.warning(f"📦 Debit: {db['pending_debit']:,.2f} LE")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Opening Checklist**")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, key="oc", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total: {t_open:,.2f} LE**")
        with c3:
            st.write("**Start Counters**")
            k_start = st.number_input("Kyocera Start", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            opay_start = st.number_input("Opay Opening Balance", step=0.01, format="%.2f", key="ops", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Financial Input**")
            sys_sales = st.number_input("System Sales (SQL)", min_value=0.0, step=1.0, key="c_sys_sales", on_change=sync_draft)
            debit_val = st.number_input("Debit (Unpaid)", min_value=0.0, step=1.0, key="c_debit", on_change=sync_draft)
            instapay = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1.0, key="c_visa", on_change=sync_draft)
            t_e_pay = instapay + wallet + visa
        with c2:
            st.write("**Closing Cash & Opay Analysis**")
            opay_end = st.number_input("Opay Closing Balance", step=0.01, format="%.2f", key="op_end", on_change=sync_draft)
            opay_diff = opay_start - opay_end # رصيد قل = مبيعات زادت في الدرج | رصيد زاد = دفعنا للمندوب من الدرج
            
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            t_close += st.number_input("Closing Coins ", step=0.5, key="cc", on_change=sync_draft)
            expenses = st.number_input("Expenses (Other)", step=1.0, key="c_exp", on_change=sync_draft)
            
            # الربط الحسابي: فرق Opay يدخل في الحسبة
            expected_cash = t_open + sys_sales + opay_diff - expenses - debit_val - t_e_pay
            net_diff = t_close - expected_cash
            st.metric("Expected Cash", f"{expected_cash:,.2f} LE")
            st.info(f"Opay Effect: {'Sales +' if opay_diff > 0 else 'Refill -'}{abs(opay_diff):,.2f}")
            if abs(net_diff) < 0.1: st.success("✅ Match")
            else: st.error(f"⚠️ Diff: {net_diff:,.2f}")
        with c3:
            st.write("**Printers**")
            k_end = st.number_input("K-End", step=1, key="k1end")
            k_actual = k_end - k_start
            st.write(f"K-Used: {k_actual}")
            x_end = st.number_input("X-End", step=1, key="x2end")
            x_actual = x_end - x_start
            st.write(f"X-Used: {x_actual}")

    with tab3:
        st.subheader("Social Media Tasks")
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["social"]): m_cols[i%4].checkbox(task, key=f"m_{task}", on_change=sync_draft)

    # --- 6. Exporting ---
    st.divider()
    wa_msg = f"*🚀 NMS REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n*💰 FINANCIALS:*\n- Sales: {sys_sales}\n- Opay Diff: {opay_diff:,.2f}\n- E-Pay: {t_e_pay}\n- Cash Drawer: {t_close:,.2f}\n- *Status:* {net_diff}\n\n*📱 OPAY DETAIL:*\n- Start: {opay_start}\n- End: {opay_end}"
    
    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD PDF REPORT", use_container_width=True):
            db["pending_debit"] = debit_val; save_db(db)
            buffer = io.BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet(); elements = []
            elements.append(Paragraph(f"NMS DAILY REPORT - {branch}", styles['Title']))
            
            data_f = [["Item", "Amount"], ["System Sales", sys_sales], ["Opay Net Diff", opay_diff], ["Electronic Pay", t_e_pay], ["Expenses", expenses], ["Expected Cash", expected_cash], ["Actual Cash", t_close], ["Net Difference", net_diff]]
            t1 = Table(data_f, colWidths=[200, 100])
            t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
            elements.append(Paragraph("1. Financial Summary", styles['Heading3'])); elements.append(t1)
            
            data_o = [["Opay Start", "Opay End", "Difference"], [opay_start, opay_end, opay_diff]]
            t2 = Table(data_o, colWidths=[100, 100, 100])
            t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
            elements.append(Spacer(1,15)); elements.append(Paragraph("2. Opay Tracking", styles['Heading3'])); elements.append(t2)
            
            doc.build(elements)
            st.download_button("💾 Save PDF", data=buffer.getvalue(), file_name=f"NMS_{branch}.pdf")

    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
