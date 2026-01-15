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

# ==========================================
# 1. DATABASE & CONFIGURATION (محرك البيانات)
# ==========================================
DB_FILE = 'nms_enterprise_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "HQ", "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [],
            "drafts": {},
            "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        if "history" not in data: data["history"] = []
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# ==========================================
# 2. CORE SERVICES (خدمات النظام)
# ==========================================

def sync_draft():
    """حفظ المسودات تلقائياً لضمان عدم ضياع البيانات"""
    if st.session_state.get('logged_in'):
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_'))}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

def generate_pdf_report(branch, staff, financial_data, printer_data):
    """توليد ملف PDF احترافي"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"NMS DAILY REPORT - {branch}", styles['Title']))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')} | Staff: {staff}", styles['Normal']))
    
    # جدول الماليات
    t1 = Table(financial_data, colWidths=[200, 100])
    t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.indianred), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke)]))
    elements.append(Spacer(1, 15)); elements.append(Paragraph("1. Financial Summary", styles['Heading3'])); elements.append(t1)

    # جدول الطابعات
    t2 = Table(printer_data, colWidths=[100, 60, 60, 60, 60])
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightblue)]))
    elements.append(Spacer(1, 15)); elements.append(Paragraph("2. Printer Analysis", styles['Heading3'])); elements.append(t2)

    doc.build(elements)
    return buffer.getvalue()

# ==========================================
# 3. UI COMPONENTS (مكونات الواجهة)
# ==========================================

def render_login_page():
    """واجهة تسجيل الدخول"""
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

def render_sidebar():
    """القائمة الجانبية"""
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
        
        return render_admin_controls() if st.session_state['role'] == 'admin' else None

def render_admin_controls():
    """لوحة تحكم المدير"""
    st.divider()
    st.subheader("🛠️ Admin Master Control")
    mode = st.radio("Settings", ["Review History", "Manage Employees", "Manage Branches", "Manage Tasks", "Audit Logs"])
    
    if mode == "Review History":
        render_admin_history()
    elif mode == "Manage Employees":
        render_admin_employees()
    elif mode == "Manage Branches":
        render_admin_branches()
    elif mode == "Manage Tasks":
        render_admin_tasks()
    elif mode == "Audit Logs":
        st.dataframe(pd.DataFrame(db["logs"]).tail(50))

# --- وظائف الإدارة الفرعية ---
def render_admin_history():
    st.subheader("📜 Shift Archive Explorer")
    if not db["history"]:
        st.warning("No records found.")
        return
    hist_df = pd.DataFrame(db["history"])
    search_date = st.date_input("Filter by Date", datetime.now())
    search_branch = st.selectbox("Filter by Branch", ["All"] + db["branches"])
    
    filtered = hist_df[hist_df['date'] == str(search_date)]
    if search_branch != "All": filtered = filtered[filtered['branch'] == search_branch]
    
    if not filtered.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Sales", f"{filtered['sales'].sum():,.2f}")
        m2.metric("Total Net Diff", f"{filtered['net_diff'].sum():,.2f}")
        m3.metric("Opay Activity", f"{filtered['opay_move'].sum():,.2f}")
        m4.metric("Shifts Count", len(filtered))
        for _, row in filtered.iterrows():
            with st.expander(f"📄 Report: {row['staff']} | {row['branch']} | {row['shift']}"):
                st.dataframe(pd.DataFrame([row]), hide_index=True)

def render_admin_employees():
    st.subheader("👥 Employee Master Control")
    with st.expander("➕ Register New Employee"):
        new_u = st.text_input("Username")
        new_p = st.text_input("Password", type="password")
        if st.button("Create Account"):
            if new_u and new_u not in db["users"]:
                db["users"][new_u] = {"pass": new_p, "role": "user", "full_name": new_u}
                save_db(db); st.success("Created!"); st.rerun()
    # تعديل بيانات الموظفين الحاليين كما فكودك الأصلي...
    target_user = st.selectbox("Select Employee", list(db["users"].keys()))
    db["users"][target_user]["full_name"] = st.text_input("Full Name", db["users"][target_user].get("full_name", ""))
    if st.button("💾 Save Changes"): save_db(db); st.success("Updated!")

def render_admin_branches():
    st.subheader("🏢 Branch Management")
    n_br = st.text_input("New Branch Name")
    if st.button("Add Branch"):
        db["branches"].append(n_br); save_db(db); st.rerun()

def render_admin_tasks():
    st.subheader("📝 Task Management")
    cat = st.selectbox("Category", ["Opening", "Closing", "Social"])
    new_t = st.text_input("Add Task")
    if st.button("➕ Add"): db["tasks"][cat.lower()].append(new_t); save_db(db); st.rerun()

# ==========================================
# 4. MAIN APPLICATION DASHBOARD
# ==========================================

def render_main_dashboard():
    st.title("📊 Daily Shift Control")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with inf2: st.info(f"🕒 **Day:** {datetime.now().strftime('%A')}")
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL MEDIA"])

    with tab1:
        t_open, k_start, x_start, opay_start, u10_debit = render_opening_tab()
    with tab2:
        expected_cash, t_close, net_diff, k_actual, x_actual, opay_diff, opay_end, k_vals, x_vals, sys_sales, expenses, t_e_pay, v22_debit = render_closing_tab(t_open, k_start, x_start, opay_start, u10_debit)
    with tab3:
        render_social_tab()

    # --- Export Section ---
    st.divider()
    diff_status = "✅ Match" if abs(net_diff) < 0.1 else f"⚠️ {net_diff}"
    wa_msg = f"*🚀 NMS FULL REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n*💰 FINANCIALS:*\n- Opening: {t_open:,.2f}\n- Sales: {sys_sales:,.2f}\n- Drawer: {t_close:,.2f}\n- *Status:* {diff_status}"

    if st.button("🏁 SUBMIT & ARCHIVE FULL SHIFT DATA", use_container_width=True):
        archive_shift(branch, shift, t_open, sys_sales, u10_debit, expenses, t_e_pay, v22_debit, expected_cash, t_close, net_diff, opay_diff, opay_end, k_actual, x_actual)

    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD FULL PDF REPORT", use_container_width=True):
            fin_data = [["Item", "Amount"], ["Opening Cash", t_open], ["Total Sales", sys_sales], ["Actual Cash", t_close], ["Net Difference", net_diff]]
            prn_data = [["Printer", "Used", "Sold", "Err", "Test"], ["Kyocera", k_actual, k_vals[0], k_vals[1], k_vals[2]], ["Xerox", x_actual, x_vals[0], x_vals[1], x_vals[2]]]
            pdf_bytes = generate_pdf_report(branch, st.session_state['user'], fin_data, prn_data)
            st.download_button("💾 Save PDF Report", data=pdf_bytes, file_name=f"NMS_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf")
    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND FULL WHATSAPP REPORT</button></a>', unsafe_allow_html=True)

def render_opening_tab():
    st.subheader("Opening Procedures")
    if db.get("pending_debit", 0) > 0:
        st.warning(f"📦 تنبيه: يوجد (Debit) مُرحل: {db['pending_debit']:,.2f} جنيه.")
    c1, c2, c3 = st.columns([1, 1.5, 1.5])
    with c1:
        st.write("**Checklist**")
        for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
    with c2:
        st.write("**Opening Cash**")
        t_o = sum([st.number_input(f"{d} LE", min_value=0, key=f"o_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
        t_o += st.number_input("Coins", step=0.5, key="oc", on_change=sync_draft)
        st.success(f"**Total: {t_o:,.2f}**")
    with c3:
        ks = st.number_input("Kyo Start", step=1, key="ks", on_change=sync_draft)
        xs = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
        ops = st.number_input("Opay Start", format="%.4f", key="ops", on_change=sync_draft)
        u10 = st.number_input("Debit Received", step=1.0, key="u10_val", on_change=sync_draft)
    return t_o, ks, xs, ops, u10

def render_closing_tab(t_open, k_start, x_start, opay_start, u10_debit):
    st.subheader("Closing Procedures")
    c1, c2, c3 = st.columns([1, 1.5, 1.5])
    with c1:
        for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
        sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales", on_change=sync_draft)
        v22_debit = st.number_input("Debit Pending", step=1.0, key="v22_val", on_change=sync_draft)
        t_e_pay = st.number_input("Instapay", key="c_insta") + st.number_input("Wallet", key="c_wall") + st.number_input("Visa", key="c_visa")
    with c2:
        t_c = sum([st.number_input(f"{d} LE ", min_value=0, key=f"c_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
        t_c += st.number_input("Closing Coins ", step=0.5, key="cc", on_change=sync_draft)
        expenses = st.number_input("Expenses", step=1.0, key="c_exp", on_change=sync_draft)
        expected = t_open + sys_sales + u10_debit - expenses - v22_debit - t_e_pay
        net_diff = t_c - expected
        st.metric("Expected Drawer", f"{expected:,.2f}")
        if abs(net_diff) < 0.1: st.success("Match")
        else: st.error(f"Diff: {net_diff:,.2f}")
    with c3:
        op_end = st.number_input("Opay Final", format="%.4f", key="op_end", on_change=sync_draft)
        k_end = st.number_input("Kyo End", key="k1end")
        k_actual = k_end - k_start
        x_end = st.number_input("Xerox End", key="x2end")
        x_actual = x_end - x_start
    return expected, t_c, net_diff, k_actual, x_actual, opay_start - op_end, op_end, [0,0,0], [0,0,0], sys_sales, expenses, t_e_pay, v22_debit

def render_social_tab():
    st.subheader("Social Media Tasks")
    cols = st.columns(4)
    for i, t in enumerate(db["tasks"]["social"]): cols[i%4].checkbox(t, key=f"m_{t}", on_change=sync_draft)

def archive_shift(branch, shift, t_open, sys_sales, u10_debit, expenses, t_e_pay, v22_debit, expected_cash, t_close, net_diff, opay_diff, opay_end, k_actual, x_actual):
    archive_data = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "staff": st.session_state['user'],
        "branch": branch,
        "shift": shift,
        "sales": sys_sales,
        "actual_cash": t_close,
        "net_diff": net_diff,
        "opay_move": opay_diff,
        "kyo_used": k_actual,
        "xerox_used": x_actual
    }
    db["history"].append(archive_data)
    db["pending_debit"] = v22_debit
    save_db(db)
    st.success("Shift Archived!")

# ==========================================
# 5. EXECUTION ENTRY POINT
# ==========================================

st.set_page_config(page_title="NMS Management System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

if not st.session_state['logged_in']:
    render_login_page()
else:
    render_sidebar()
    render_main_dashboard()
