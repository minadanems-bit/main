import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image

# --- 1. وظائف قاعدة البيانات والصور ---
DB_FILE = 'nms_db.json'

def load_data():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "General Manager", "photo": None}
            },
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {
                "start": ["Finger print", "Power on", "Uniform", "Music on", "Paper loaded", "Cash counted"],
                "end": ["Contacts", "Place cleaned", "Power off", "Cash counted", "Report sent"],
                "marketing": ["WhatsApp", "FB Story", "Instagram", "TikTok", "LinkedIn"]
            }
        }
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

# تحويل الصورة لنص لحفظها
def image_to_base64(image_file):
    if image_file is not None:
        return base64.b64encode(image_file.getvalue()).decode()
    return None

db = load_data()

# --- 2. إعداد الصفحة ---
st.set_page_config(page_title="NMS System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None})

# --- 3. تسجيل الدخول (اللغتين) ---
if not st.session_state['logged_in']:
    st.title("🔐 Login | تسجيل الدخول")
    col_l, col_r = st.columns(2)
    with col_l:
        u = st.selectbox("Select User | اختر المستخدم", list(db["users"].keys()))
        p = st.text_input("Password | كلمة المرور", type="password")
        if st.button("Login | دخول", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u})
                st.rerun()
            else: st.error("Wrong Password | كلمة مرور خاطئة")

else:
    # --- القائمة الجانبية (حفظ الصورة الشخصية) ---
    with st.sidebar:
        st.header(f"Welcome | أهلاً {st.session_state['user']}")
        
        # عرض الصورة المحفوظة مسبقاً إن وجدت
        current_user = st.session_state['user']
        user_photo = db["users"][current_user].get("photo")
        
        if user_photo:
            st.image(base64.b64decode(user_photo), width=150)
        
        new_photo = st.file_uploader("Change Photo | تغيير الصورة", type=['png', 'jpg'])
        if new_photo:
            db["users"][current_user]["photo"] = image_to_base64(new_photo)
            save_data(db)
            st.success("Photo Saved! | تم حفظ الصورة")
            st.rerun()

        if st.button("Logout | خروج"):
            st.session_state['logged_in'] = False
            st.rerun()

        # لوحة التحكم للمدير (تعديل البيانات)
        if db["users"][current_user]["role"] == "admin":
            st.divider()
            st.subheader("Admin Control | لوحة المدير")
            target = st.selectbox("Edit Employee | تعديل موظف", list(db["users"].keys()))
            new_full_name = st.text_input("Full Name | الاسم بالكامل", value=db["users"][target].get("full_name", ""))
            if st.button("Save Changes | حفظ"):
                db["users"][target]["full_name"] = new_full_name
                save_data(db)
                st.success("Updated! | تم التحديث")

    # --- واجهة العمل (اللغتين) ---
    st.title("📊 Shift Management | إدارة الشفت")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')} | {datetime.now().strftime('%A')}")
    with c2: branch = st.selectbox("Branch | الفرع", db["branches"])
    with c3: shift = st.selectbox("Shift | الشفت", ["Morning", "Between", "Night"])

    t1, t2, t3 = st.tabs(["🟢 Start | البداية", "🔴 End | النهاية", "📱 Marketing | التسويق"])

    with t1:
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("💰 Opening Cash | نقدية الفتح")
            total_open = 0
            for d in [200, 100, 50, 20, 10, 5]:
                val = st.number_input(f"{d} LE", min_value=0, step=1, format="%d", key=f"o_{d}")
                total_open += (val * d)
            st.metric("Total Open | الإجمالي", f"{total_open} LE")
        with col_r:
            st.subheader("🖨️ Counters | العدادات")
            k_start = st.number_input("Kyocera Start | بداية كيوسيرا", step=1, format="%d")
            x_start = st.number_input("Xerox Start | بداية زيروكس", step=1, format="%d")

    with t2:
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("💰 Closing Cash | نقدية الغلق")
            total_close = 0
            for d in [200, 100, 50, 20, 10, 5]:
                val = st.number_input(f"{d} LE  ", min_value=0, step=1, format="%d", key=f"c_{d}")
                total_close += (val * d)
            exp = st.number_input("Expenses | المصاريف", step=1, format="%d")
            net = (total_close + exp) - total_open
            st.metric("Difference | الفرق", f"{net} LE")
        with col_r:
            st.subheader("📊 Usage | الاستهلاك")
            k_end = st.number_input("Kyocera End | نهاية كيوسيرا", step=1, format="%d")
            x_end = st.number_input("Xerox End | نهاية زيروكس", step=1, format="%d")
            st.write(f"Total Pages | إجمالي الصفحات: {(k_end - k_start) + (x_end - x_start)}")

    # --- زر التقرير PDF ---
    st.divider()
    if st.button("📥 Download Report | تحميل التقرير", type="primary", use_container_width=True):
        st.balloons()
        st.success("Report Ready! | التقرير جاهز")
