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
# 1. DATABASE & CONFIGURATION
# ==========================================
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
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "expense_categories": ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Other"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform", "Cash Counted"],
                "closing": ["Place Cleaned", "Power Off", "Report Sent"],
                "social": ["Facebook", "Instagram", "TikTok", "WhatsApp", "Threads", "LinkedIn"]
            },
            "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        if "expense_categories" not in data: data["expense_categories"] = ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Other"]
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# ==========================================
# 2. LOGIN & ADMIN UI
# ==========================================
def render_login_page():
    st.title("🚀 NMS ERP - Enterprise Login")
    u = st.selectbox("Select Employee", list(db["users"].keys()))
    p = st.text_input("Password", type="password")
    if st.button("Login to System", use_container_width=True):
        if db["users"][u]["pass"] == p:
            st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
            st.rerun()
        else: st.error("Authentication Failed")

def render_admin_controls():
    st.sidebar.divider()
    st.sidebar.subheader("🛠️ Admin Master Control")
    mode = st.sidebar.radio("Settings", ["Review History", "Manage Expenses", "Manage Employees"])
    
    if mode == "Manage Expenses":
        st.subheader("💰 Manage Expense Categories (إدارة بنود المصاريف)")
        new_cat = st.text_input("New Expense Category (بند جديد)")
        if st.button("➕ Add Category"):
            if new_cat and new_cat not in db["expense_categories"]:
                db["expense_categories"].append(new_cat)
                save_db(db); st.success(f"Added: {new_cat}"); st.rerun()
        
        st.divider()
        cat_to_del = st.selectbox("Select Category to Delete", db["expense_categories"])
        if st.button("🗑️ Delete Selected Category", type="primary"):
            if len(db["expense_categories"]) > 1:
                db["expense_categories"].remove(cat_to_del)
                save_db(db); st.warning("Deleted!"); st.rerun()
    
    elif mode == "Review History":
        st.subheader("📜 Shift Archive")
        if db["history"]:
            st.dataframe(pd.DataFrame(db["history"]))
        else: st.info("No records yet.")
            # ==========================================
# 3. MAIN DASHBOARD & OPERATIONS (الجزء الثاني)
# ==========================================

def render_main_dashboard():
    st.title("📊 Daily Shift Operations")
    
    # اختيار الفرع والوردية
    c1, c2, c3 = st.columns(3)
    with c1: branch = st.selectbox("Branch (الفرع)", db["branches"])
    with c2: shift = st.selectbox("Shift (الوردية)", ["Morning", "Night"])
    with c3: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING (الافتتاح)", "🔴 CLOSING (التقفيل)", "📱 SOCIAL (السوشيال)"])

    with tab1:
        st.subheader("Opening Checklist & Cash")
        col_op1, col_op2 = st.columns(2)
        with col_op1:
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}")
        with col_op2:
            op_cash = st.number_input("Opening Cash (عهدة البداية)", min_value=0.0)
            k_start = st.number_input("Kyocera Start (عداد كيو)", step=1)
            x_start = st.number_input("Xerox Start (عداد زيروكس)", step=1)

    with tab2:
        st.subheader("Financial Closing")
        cl_left, cl_right = st.columns(2)
        
        with cl_left:
            sys_sales = st.number_input("System Sales (مبيعات السيستم)", min_value=0.0)
            
            # --- تطوير خانة المصاريف ---
            st.markdown("---")
            st.write("💰 **Expenses (المصاريف)**")
            exp_cat = st.selectbox("بند المصروف", db["expense_categories"])
            exp_amt = st.number_input("مبلغ المصروف", min_value=0.0)
            exp_note = st.text_input("تفاصيل/ملاحظات المصروف")
            exp_details = f"{exp_cat}: {exp_note}" if exp_note else exp_cat
            st.markdown("---")

        with cl_right:
            actual_cash = st.number_input("Actual Cash in Drawer (الموجود فعلياً)", min_value=0.0)
            k_end = st.number_input("Kyocera End (عداد كيو نهاية)", step=1)
            x_end = st.number_input("Xerox End (عداد زيروكس نهاية)", step=1)

        # الحسابات
        expected = op_cash + sys_sales - exp_amt
        diff = actual_cash - expected
        
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Expected (المفروض)", f"{expected:,.2f}")
        m2.metric("Actual (الفعلي)", f"{actual_cash:,.2f}")
        m3.metric("Difference (عجز/زيادة)", f"{diff:,.2f}", delta=diff)

    with tab3:
        st.subheader("Social Media Tasks")
        cols = st.columns(3)
        for i, t in enumerate(db["tasks"]["social"]):
            cols[i%3].checkbox(t, key=f"soc_{t}")

    # زر الحفظ والإرسال
    st.divider()
    if st.button("🏁 SUBMIT & SEND REPORT (إرسال التقرير النهائي)", use_container_width=True):
        # حفظ في الأرشيف
        new_entry = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "branch": branch,
            "staff": st.session_state['user'],
            "sales": sys_sales,
            "expenses": exp_amt,
            "exp_details": exp_details,
            "actual": actual_cash,
            "diff": diff,
            "kyo_used": k_end - k_start,
            "xerox_used": x_end - x_start
        }
        db["history"].append(new_entry)
        save_db(db)
        st.success("✅ Shift Archived Successfully!")

        # إرسال واتساب للمدير
        wa_text = f"*🚀 NMS DAILY REPORT*\n*Branch:* {branch}\n*Staff:* {st.session_state['user']}\n\n"
        wa_text += f"💰 *Financials:*\n- Opening: {op_cash}\n- Sales: {sys_sales}\n- Exp: {exp_details} (-{exp_amt})\n"
        wa_text += f"- Expected: {expected}\n- Actual: {actual_cash}\n- *Status:* {'OK' if diff==0 else f'Diff {diff}'}\n\n"
        wa_text += f"🖨️ *Printers:*\n- Kyo: {k_end - k_start}\n- Xerox: {x_end - x_start}"
        
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 OPEN WHATSAPP TO SEND REPORT</button></a>', unsafe_allow_html=True)

# ==========================================
# 4. EXECUTION
# ==========================================
st.set_page_config(page_title="NMS ERP", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    render_login_page()
else:
    if st.session_state['role'] == 'admin':
        render_admin_controls()
    render_main_dashboard()
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False; st.rerun()
