import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import io

# --- 1. إعدادات قاعدة البيانات ---
DB_FILE = 'nms_db.json'

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "General Manager", "phone": "000", "id_num": "000", "address": "Office", "email": "admin@nms.com"},
                "Mina": {"pass": "1234", "role": "user", "full_name": "Mina", "phone": "", "id_num": "", "address": "", "email": ""},
                "Youstina": {"pass": "1234", "role": "user", "full_name": "Youstina", "phone": "", "id_num": "", "address": "", "email": ""},
                "Mark": {"pass": "1234", "role": "user", "full_name": "Mark", "phone": "", "id_num": "", "address": "", "email": ""},
                "Fatma": {"pass": "1234", "role": "user", "full_name": "Fatma", "phone": "", "id_num": "", "address": "", "email": ""}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger print", "Power on", "Uniform and name tag", "Music on", "Paper loaded", "Cash counted", "All good"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Finger print", "Report sent"],
                "marketing": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "FB Story", "FB Post/Reel", "FB Group", "Page Story", "Page Post/Reel", "Threads", "Instagram Story", "Instagram Post/Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post", "Like", "Love", "Care", "Share"]
            }
        }
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

db = load_data()

# --- 2. إعداد الصفحة ---
st.set_page_config(page_title="NMS Shift System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# --- 3. نظام تسجيل الدخول ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - تسجيل الدخول")
    col_l, col_r = st.columns(2)
    with col_l:
        logo = st.file_uploader("ارفع لوجو الشركة (هوية بصرية)", type=['png', 'jpg', 'jpeg'])
        if logo: st.image(logo, width=200)
    
    with col_r:
        u = st.selectbox("الموظف", list(db["users"].keys()))
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
                st.rerun()
            else: st.error("كلمة المرور خطأ")

else:
    # --- القائمة الجانبية (Sidebar) ---
    with st.sidebar:
        st.header(f"أهلاً {st.session_state['user']}")
        emp_photo = st.file_uploader("ارفع صورتك الشخصية", type=['png', 'jpg'])
        if emp_photo: st.image(emp_photo, width=150)
        
        if st.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ لوحة تحكم المدير")
            
            # تعديل/إضافة موظفين
            mode = st.radio("الوضع", ["إضافة موظف جديد", "تعديل بيانات موظف"])
            
            if mode == "إضافة موظف جديد":
                new_u = st.text_input("اسم المستخدم (للدخول)")
                new_p = st.text_input("الباسورد")
                if st.button("إضافة"):
                    db["users"][new_u] = {"pass": new_p, "role": "user", "full_name": new_u, "phone": "", "id_num": "", "address": "", "email": ""}
                    save_data(db)
                    st.success("تم الإضافة")
            
            else:
                target_u = st.selectbox("اختر الموظف للتعديل", list(db["users"].keys()))
                edit_full_name = st.text_input("الاسم بالكامل", value=db["users"][target_u].get("full_name", ""))
                edit_pass = st.text_input("تغيير الباسورد", value=db["users"][target_u].get("pass", ""))
                edit_phone = st.text_input("رقم الموبايل", value=db["users"][target_u].get("phone", ""))
                edit_email = st.text_input("البريد الإلكتروني", value=db["users"][target_u].get("email", ""))
                edit_address = st.text_input("العنوان السكني", value=db["users"][target_u].get("address", ""))
                edit_id = st.text_input("رقم الهوية", value=db["users"][target_u].get("id_num", ""))
                
                if st.button("حفظ التعديلات"):
                    db["users"][target_u].update({
                        "pass": edit_pass, "full_name": edit_full_name, "phone": edit_phone,
                        "email": edit_email, "address": edit_address, "id_num": edit_id
                    })
                    save_data(db)
                    st.success("تم التحديث بنجاح")

    # --- واجهة العمل الرئيسية ---
    st.title("📊 نظام تقارير الشفت اليومي")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')} | {datetime.now().strftime('%A')}")
    with c2:
        branch = st.selectbox("الفرع", db["branches"])
    with c3:
        shift_type = st.selectbox("الشفت", ["Morning", "Between", "Night"])

    t1, t2, t3 = st.tabs(["🟢 بداية الشفت (Start)", "🔴 نهاية الشفت (End)", "📱 السوشيال ميديا (Marketing)"])

    # --- TAB 1: START ---
    with t1:
        col_chk, col_cash, col_pr = st.columns([1, 1, 1])
        with col_chk:
            st.subheader("Checklist")
            s_results = {task: st.checkbox(task, key=f"s_{task}") for task in db["tasks"]["start"]}
        
        with col_cash:
            st.subheader("💰 Opening Cash")
            total_open = 0
            denoms = [200, 100, 50, 20, 10, 5]
            for d in denoms:
                # استخدمنا value=0 و step=1 و format لتمكين الكتابة من الكيبورد
                num = st.number_input(f"{d} LE", min_value=0, step=1, format="%d", key=f"o_{d}")
                total_open += (num * d)
            o_coins = st.number_input("Coins", min_value=0, step=1, format="%d", key="o_coins")
            total_open += o_coins
            st.metric("إجمالي الفتح", f"{total_open} LE")

        with col_pr:
            st.subheader("🖨️ Opening Counters")
            k_start = st.number_input("Kyocera Start", step=1, format="%d")
            x_start = st.number_input("Xerox Start", step=1, format="%d")
            opay_start = st.number_input("Opay Opening Balance", step=1, format="%d")

    # --- TAB 2: END ---
    with t2:
        col_chk2, col_cash2, col_pr2 = st.columns([1, 1, 1])
        with col_chk2:
            st.subheader("Checklist")
            e_results = {task: st.checkbox(task, key=f"e_{task}") for task in db["tasks"]["end"]}
            st.divider()
            st.subheader("💳 المعاملات غير النقدية")
            i_pay = st.number_input("Instapay", step=1, format="%d")
            w_pay = st.number_input("Wallet", step=1, format="%d")
            v_pay = st.number_input("Visa", step=1, format="%d")
            non_cash_total = i_pay + w_pay + v_pay

        with col_cash2:
            st.subheader("💰 Closing Cash")
            total_close = 0
            for d in denoms:
                num = st.number_input(f"{d} LE ", min_value=0, step=1, format="%d", key=f"c_{d}")
                total_close += (num * d)
            c_coins = st.number_input("Coins ", min_value=0, step=1, format="%d", key="c_coins")
            total_close += c_coins
            expenses = st.number_input("Expenses (المصاريف)", step=1, format="%d")
            
            # الحساب التلقائي
            net_diff = (total_close + expenses) - total_open
            st.metric("صافي العجز / الزيادة", f"{net_diff} LE")

        with col_pr2:
            st.subheader("🖨️ Final Counters")
            k_end = st.number_input("Kyocera End", step=1, format="%d")
            x_end = st.number_input("Xerox End", step=1, format="%d")
            total_pages = (k_end - k_start) + (x_end - x_start)
            st.write(f"إجمالي المطبوع: {total_pages}")
            
            st.write("--- تفاصيل الطباعة ---")
            oneside = st.number_input("One Side", step=1, format="%d")
            duplex = st.number_input("Duplex", step=1, format="%d")
            draft = st.number_input("Draft", step=1, format="%d")
            
            st.divider()
            opay_end = st.number_input("Opay Balance End", step=1, format="%d")
            st.write(f"Opay Difference: {opay_end - opay_start}")

    # --- TAB 3: MARKETING ---
    with t3:
        st.subheader("📱 Social Media Checklist")
        m_cols = st.columns(4)
        m_results = {}
        for i, task in enumerate(db["tasks"]["marketing"]):
            m_results[task] = m_cols[i % 4].checkbox(task, key=f"m_{task}")

    # --- PDF GENERATION ---
    st.divider()
    if st.button("📥 استخراج تقرير PDF الشامل", type="primary", use_container_width=True):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph(f"NMS Shift Report - {branch}", styles['Title']))
        elements.append(Paragraph(f"Employee: {st.session_state['user']} | Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # جداول البيانات في PDF
        data = [
            ["Category", "Detail", "Value"],
            ["Cash", "Opening", f"{total_open} LE"],
            ["", "Closing", f"{total_close} LE"],
            ["", "Expenses", f"{expenses} LE"],
            ["", "Difference", f"{net_diff} LE"],
            ["Printers", "Total Pages", f"{total_pages}"],
            ["", "OneSide/Duplex/Draft", f"{oneside}/{duplex}/{draft}"],
            ["Opay", "Balance Diff", f"{opay_end - opay_start} LE"],
            ["Non-Cash", "Total", f"{non_cash_total} LE"]
        ]
        t = Table(data, colWidths=[100, 150, 100])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t)
        
        doc.build(elements)
        st.download_button("Download PDF", data=buffer.getvalue(), file_name=f"Report_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
        st.balloons()
