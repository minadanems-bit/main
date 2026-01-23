# pages/user_view.py

import streamlit as st
from database import load_db, save_db

# إعداد الصفحة
st.set_page_config(page_title="User View", page_icon="👤", layout="wide")

# تحميل قاعدة البيانات
db = load_db()

# التأكد من صلاحية الدخول
if st.session_state.get("role") != "user":
    st.error("You are not authorized to view this page.")
    st.stop()

# الترحيب بالمستخدم
user = st.session_state.get("user", "Unknown")
user_data = db["users"].get(user, {})

st.title(f"👋 Welcome, {user_data.get('full_name', user)}")

st.markdown("---")

# عرض بعض البيانات الخاصة بالمستخدم
st.subheader("📋 Your Info")

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Username:** {user}")
    st.write(f"**Phone:** {user_data.get('phone', 'N/A')}")
    st.write(f"**Email:** {user_data.get('email', 'N/A')}")

with col2:
    st.write(f"**Salary:** {user_data.get('salary', 0):,.2f}")
    st.write(f"**Role:** {user_data.get('role', 'user')}")
    st.write(f"**Hired on:** {user_data.get('hiring_date', 'N/A')}")

# يمكن إضافة أقسام أخرى حسب الحاجة
