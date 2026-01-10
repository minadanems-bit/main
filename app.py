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
            "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager"},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina"}
            },
            "branches": ["M. Nagib Branch", "Tram Branch"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook Story", "Facebook Reel", "Facebook Group", "Threads", "Instagram Story", "Instagram Reel", "TikTok", "Telegram", "LinkedIn"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [],
            "drafts": {}
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Session & Sync ---
st.set_page_config(page_title="NMS Enterprise System", layout="wide")
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_'))}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# --- 3. Login ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Login")
    u = st.selectbox("Employee", list(db["users"].keys()))
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if db["users"][u]["pass"] == p:
            st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
            if u in db.get("drafts", {}):
                for key, val in db["drafts"][u].items(): st.session_state[key] = val
            st.rerun()
else:
    # --- 4. Main UI ---
    st.sidebar.header(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("Logout"): st.session_state['logged_in'] = False; st.rerun()

    st.title("📊 Daily Shift Management")
    col_info = st.columns(4)
    with col_info[0]: branch = st.selectbox("Branch", db["branches"])
    with col_info[1]: shift = st.selectbox("Shift", ["Morning", "Night"])
    
    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING", "🔴 TAB 2: CLOSING", "📱 TAB 3: SOCIAL"])

    with tab1:
        st.subheader("Opening Details")
        if db.get("pending_debit", 0) > 0:
            st.warning(f"⚠️ DEBIT Alert: There is {db['pending_debit']:,.2f} LE from previous shift to be collected.")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.write("**Opening Checklist**")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, key="oc", on_change=sync_draft)
            t_open += o_coins
            st.success(f"Total Opening: {t_open:,.2f}")
        with c3:
            st.write("**Opening Counters**")
            k_start = st.number_input("Kyocera Start", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            op_start = st.number_input("Opay Start", step=0.01, key="ops", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Details")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            sys_sales = st.number_input("System Sales (SQL)", min_value=0.0, key="c_sys_sales", on_change=sync_draft)
            debit_val = st.number_input("Debit (Unpaid Orders)", min_value=0.0, key="c_debit", on_change=sync_draft)
        with c2:
            st.write("**Closing Cash**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Coins ", step=0.5, key="cc", on_change=sync_draft)
            t_close += c_coins
            expenses = st.number_input("Expenses", min_value=0.0, key="c_exp", on_change=sync_draft)
            
            expected_cash = t_open + sys_sales - expenses - debit_val
            diff = t_close - expected_cash
            st.metric("Expected Cash", f"{expected_cash:,.2f}")
            st.metric("Difference", f"{diff:,.2f}", delta_color="normal")
        with c3:
            st.write("**Closing Counters**")
            k_end = st.number_input("Kyo End", step=1, key="k1end", on_change=sync_draft)
            x_end = st.number_input("Xerox End", step=1, key="x2end", on_change=sync_draft)
            k_actual = k_end - k_start
            x_actual = x_end - x_start
            st.info(f"Kyo Used: {k_actual} | Xerox Used: {x_actual}")

    with tab3:
        st.subheader("Social Media & Interaction")
        sm_cols = st.columns(4)
        for i, t in enumerate(db["tasks"]["social"]): sm_cols[i%4].checkbox(t, key=f"m_{t}", on_change=sync_draft)
        st.divider()
        int_cols = st.columns(4)
        for i, t in enumerate(db["tasks"]["interaction"]): int_cols[i%4].checkbox(t, key=f"i_{t}", on_change=sync_draft)

    # --- 5. Export Logic ---
    st.divider()
    if st.button("📥 GENERATE FULL PDF & CLOSE SHIFT", use_container_width=True):
        db["pending_debit"] = debit_val
        save_db(db)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Header
        elements.append(Paragraph(f"NMS REPORT: {branch} - {datetime.now().strftime('%Y-%m-%d')}", styles['Title']))
        elements.append(Paragraph(f"Employee: {st.session_state['user']} | Shift: {shift}", styles['Normal']))
        elements.append(Spacer(1, 15))

        # Table 1: Opening Cash (Tab 1)
        elements.append(Paragraph("1. Opening Cash Breakdown (Tab 1)", styles['Heading3']))
        data_o = [["Denomination", "Count", "Total"]]
        for d in [200, 100, 50, 20, 10, 5]:
            count = st.session_state.get(f"o_{d}", 0)
            data_o.append([f"{d} LE", count, f"{count*d:,.2f}"])
        data_o.append(["Coins", "-", f"{st.session_state.get('oc', 0):,.2f}"])
        data_o.append(["TOTAL OPENING", "", f"{t_open:,.2f}"])
        t1 = Table(data_o, colWidths=[150, 100, 100])
        t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t1)
        elements.append(Spacer(1, 15))

        # Table 2: Financial Closing (Tab 2)
        elements.append(Paragraph("2. Financial Summary & Closing (Tab 2)", styles['Heading3']))
        data_f = [
            ["Item", "Value (LE)"],
            ["System Sales (SQL)", f"{sys_sales:,.2f}"],
            ["Debit (Pending)", f"{debit_val:,.2f}"],
            ["Expenses", f"{expenses:,.2f}"],
            ["Expected In Drawer", f"{expected_cash:,.2f}"],
            ["Actual In Drawer", f"{t_close:,.2f}"],
            ["Difference", f"{diff:,.2f}"]
        ]
        t2 = Table(data_f, colWidths=[200, 150])
        t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.indianred), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke)]))
        elements.append(t2)
        elements.append(Spacer(1, 15))

        # Table 3: Printer Analysis
        elements.append(Paragraph("3. Printer Counter Analysis", styles['Heading3']))
        data_p = [
            ["Printer", "Start", "End", "Used"],
            ["Kyocera", k_start, k_end, k_actual],
            ["Xerox", x_start, x_end, x_actual]
        ]
        t3 = Table(data_p, colWidths=[100, 80, 80, 80])
        t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightblue)]))
        elements.append(t3)
        elements.append(Spacer(1, 15))

        # Table 4: Tasks Progress (Tab 1 & 2)
        elements.append(Paragraph("4. Operation Tasks Checklist", styles['Heading3']))
        data_t = [["Task Description", "Status"]]
        for t in db["tasks"]["opening"]: data_t.append([f"Opening: {t}", "✅" if st.session_state.get(f"s_{t}") else "❌"])
        for t in db["tasks"]["closing"]: data_t.append([f"Closing: {t}", "✅" if st.session_state.get(f"e_{t}") else "❌"])
        t4 = Table(data_t, colWidths=[250, 100])
        t4.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t4)
        elements.append(Spacer(1, 15))

        # Table 5: Social Media (Tab 3)
        elements.append(Paragraph("5. Social Media & Interaction (Tab 3)", styles['Heading3']))
        data_s = [["Platform Task", "Status"]]
        for t in db["tasks"]["social"]: data_s.append([t, "✅" if st.session_state.get(f"m_{t}") else "❌"])
        for t in db["tasks"]["interaction"]: data_s.append([f"Interact: {t}", "✅" if st.session_state.get(f"i_{t}") else "❌"])
        t5 = Table(data_s, colWidths=[250, 100])
        t5.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgreen)]))
        elements.append(t5)

        doc.build(elements)
        st.download_button("💾 Download Professional Report", data=buffer.getvalue(), file_name=f"NMS_Full_Report_{datetime.now().strftime('%Y%m%d')}.pdf")
        
        # WhatsApp Message
        wa_msg = f"*🚀 NMS REPORT*\n*Branch:* {branch}\n*Staff:* {st.session_state['user']}\n*Sales:* {sys_sales}\n*Debit:* {debit_val}\n*Cash:* {t_close}\n*Diff:* {diff}"
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'[📱 Send Summary to WhatsApp]({wa_url})')
