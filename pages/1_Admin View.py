# pages/admin_view.py

import streamlit as st
from database import load_db, save_db

# إعداد الصفحة
st.set_page_config(page_title="Admin View", page_icon="🛠️", layout="wide")

# تحميل قاعدة البيانات
db = load_db()

# التأكد من صلاحية الدخول
if st.session_state.get("role") != "admin":
    st.error("You are not authorized to view this page.")
    st.stop()

st.title("🛠️ Admin Control Panel")

# واجهة الموظفين
st.header("👥 All Employees")

for username, info in db["users"].items():
    with st.expander(f"👤 {info.get('full_name', username)} ({username})"):
        full_name = st.text_input("Full Name", value=info.get("full_name", ""), key=f"full_{username}")
        salary = st.number_input("Salary", value=float(info.get("salary", 0)), key=f"sal_{username}")
        phone = st.text_input("Phone", value=info.get("phone", ""), key=f"phone_{username}")

        if st.button(f"💾 Save Changes for {username}"):
            db["users"][username]["full_name"] = full_name
            db["users"][username]["salary"] = salary
            db["users"][username]["phone"] = phone
            save_db(db)
            st.success(f"Saved changes for {username}")
            st.rerun()
