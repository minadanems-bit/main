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
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "HQ", "photo": None}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار", "كهرباء ومياه"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["WhatsApp Story", "Facebook Post", "Instagram Story", "TikTok Post", "Telegram Channel"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [], "drafts": {}, "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        # التأكد من وجود كافة حقول الموظفين الجديدة
        hr_fields = ["salary", "advances", "deductions", "bonus", "start_date", "marital_status", "education", "military_status"]
        for u in data["users"]:
            for field in hr_fields:
                if field not in data["users"][u]: data["users"][u][field] = "" if "salary" not in field else 0.0
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Logic & Session ---
st.set_page_config(page_title="NMS ERP Enterprise", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})
if 'exp_list' not in st.session_state:
    st.session_state.exp_list = []

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # حفظ كل المفاتيح البرمجية التي تبدأ بالرموز المحددة لضمان المسودة
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_'))}
        current_data['exp_list'] = st.session_state.exp_list
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
                    draft = db["drafts"][u]
                    for key, val in draft.items():
                        if key == 'exp_list': st.session_state.exp_list = val
                        else: st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Authentication Failed")
else:
    # --- 4. Sidebar & HR Control ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"User: {st.session_state['user']}")
        user_node = db["users"][st.session_state['user']]
        if user_node.get("photo"): st.image(base64.b64decode(user_node["photo"]), width=150)
        
        prof_pic = st.file_uploader("Update Personal Photo", type=['jpg', 'png'])
        if st.button("Save Photo"):
            if prof_pic:
                db["users"][st.session_state['user']]["photo"] = base64.b64encode(prof_pic.getvalue()).decode()
                save_db(db); st.success("Photo Updated!"); st.rerun()

        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Master Control")
            adm_mode = st.radio("Settings", ["Manage Employees", "Manage Branches/Tasks", "Review History", "Audit Logs"])
            
            if adm_mode == "Manage Employees":
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                u_data = db["users"][target]
                u_data["full_name"] = st.text_input("Full Name", u_data.get("full_name", ""))
                u_data["pass"] = st.text_input("Password", u_data["pass"])
                u_data["phone"] = st.text_input("Phone", u_data.get("phone", ""))
                u_data["address"] = st.text_input("Address", u_data.get("address", ""))
                u_data["id_num"] = st.text_input("ID Number", u_data.get("id_num", ""))
                u_data["military_status"] = st.selectbox("Military", ["N/A", "Completed", "Exempted", "Postponed"], index=0)
                if st.button("💾 Save Employee Data"): save_db(db); st.success("Saved!")

    # --- 5. Main Dashboard ---
    st.title("📊 Daily Shift Control")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with inf2: st.info(f"🕒 **Day:** {datetime.now().strftime('%A')}")
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL & SUBMIT"])

    with tab1:
        st.subheader("Opening Procedures")
        if db.get("pending_debit", 0) > 0:
            st.warning(f"📦 تنبيه هام: يوجد (Debit) مُرحل من الشفت السابق بقيمة: {db['pending_debit']:,.2f} جنيه.")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Checklist**")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = sum([st.number_input(f"{d} LE", 0, key=f"o_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
            t_open += st.number_input("Coins (Decimal)", 0.0, step=0.5, format="%.2f", key="oc", on_change=sync_draft)
            st.success(f"**Total Opening: {t_open:,.2f} LE**")
        with c3:
            st.write("**Start Counters & Debit**")
            ks = st.number_input("Kyocera Opening", 0, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Opening", 0, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Opening Balance", 0.0, format="%.4f", key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit Received (+)", 0.0, key="u10_val", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            sys_sales = st.number_input("System Sales", 0.0, key="c_sys_sales", on_change=sync_draft)
            v22 = st.number_input("Debit Pending (Out)", 0.0, key="v22_val", on_change=sync_draft)
            insta = st.number_input("Instapay", 0.0, key="c_insta", on_change=sync_draft)
            wall = st.number_input("Wallet", 0.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", 0.0, key="c_visa", on_change=sync_draft)
        with c2:
            st.write("**Expense Tracker**")
            e_col1, e_col2 = st.columns(2)
            with e_col1: e_type = st.selectbox("Category", db["exp_categories"])
            with e_col2: e_amt = st.number_input("Amount", 0.0, key="cur_exp_amt")
            e_desc = st.text_input("Details", key="cur_exp_desc")
            if st.button("➕ Add Expense"):
                st.session_state.exp_list.append({"Type": e_type, "Amount": e_amt, "Details": e_desc})
                sync_draft(); st.rerun()
            expenses = sum(x['Amount'] for x in st.session_state.exp_list)
            if st.session_state.exp_list:
                st.dataframe(pd.DataFrame(st.session_state.exp_list), hide_index=True)
                if st.button("🗑️ Clear"): st.session_state.exp_list = []; sync_draft(); st.rerun()
            
            st.divider()
            st.write("**Closing Cash**")
            t_close = sum([st.number_input(f"{d} LE  ", 0, key=f"c_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
            t_close += st.number_input("Closing Coins  ", 0.0, step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            expected = t_open + sys_sales + u10 - expenses - v22 - (insta + wall + visa)
            st.metric("Expected Drawer", f"{expected:,.2f}", delta=f"{t_close - expected:,.2f}")
        with c3:
            st.write("**Printers Analysis**")
            # دمج العدادات الدقيقة من كود مينا الأصلي
            st.markdown("### 🖨️ Kyocera")
            ke = st.number_input("Counter End", 0, key="k1end", on_change=sync_draft)
            k_os = st.number_input("One-Side", 0, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("Duplex", 0, key="k1dp", on_change=sync_draft)
            k_err = st.number_input("Errors/Jam", 0, key="k1err", on_change=sync_draft)
            k_tst = st.number_input("Test/Draft", 0, key="k1tst", on_change=sync_draft)
            k_actual = ke - ks
            k_acc = k_os + (k_dp * 2) + k_err + k_tst
            if k_acc == k_actual: st.success(f"✅ Match: {k_actual}")
            else: st.error(f"⚠️ Diff: {k_acc - k_actual}")

            st.markdown("### 🖨️ Xerox")
            xe = st.number_input("Counter End (X)", 0, key="x2end", on_change=sync_draft)
            x_os = st.number_input("One-Side (X)", 0, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("Duplex (X)", 0, key="x2dp", on_change=sync_draft)
            x_actual = xe - xs
            
            ope = st.number_input("Opay Final Balance", 0.0, format="%.4f", key="op_end", on_change=sync_draft)

    with tab3:
        st.subheader("Social Media & interaction")
        m_cols = st.columns(4)
        for i, t in enumerate(db["tasks"]["social"]): m_cols[i%4].checkbox(t, key=f"m_{t}", on_change=sync_draft)
        
        st.divider()
        # أزرار الأرشفة والواتساب في التاب الأخير فقط
        exp_details_str = ", ".join([f"{x['Type']}:{x['Amount']}" for x in st.session_state.exp_list])
        wa_msg = f"*🚀 NMS REPORT*\n*Branch:* {branch}\n*Staff:* {st.session_state['user']}\n*Sales:* {sys_sales:,.2f}\n*Expenses:* {expenses:,.2f}\n*Net Diff:* {t_close - expected:,.2f}\n*K-Used:* {k_actual}\n*X-Used:* {x_actual}"
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            if st.button("🏁 SUBMIT & ARCHIVE SHIFT", use_container_width=True):
                archive_data = {"date": str(datetime.now().date()), "staff": st.session_state['user'], "branch": branch, "sales": sys_sales, "expenses": expenses, "net_diff": t_close - expected, "kyo_used": k_actual, "xerox_used": x_actual, "opay_move": ops - ope}
                db["history"].append(archive_data); db["pending_debit"] = v22
                db["drafts"][st.session_state['user']] = {}; st.session_state.exp_list = []
                save_db(db); st.success("Shift Archived!"); st.rerun()
        with col_f2:
            if st.button("📥 DOWNLOAD PDF", use_container_width=True):
                buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=letter); elements = []
                styles = getSampleStyleSheet()
                elements.append(Paragraph(f"NMS REPORT - {branch}", styles['Title']))
                elements.append(Table([["Metric", "Value"], ["Sales", sys_sales], ["Expenses", expenses], ["Difference", t_close-expected]], colWidths=[200, 100]).setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)])))
                doc.build(elements); st.download_button("Save PDF", buf.getvalue(), f"Report_{branch}.pdf")
        with col_f3:
            wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📱 WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
