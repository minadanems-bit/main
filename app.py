import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# إعداد الصفحة
st.set_page_config(page_title="NMS System", layout="wide")

# قاعدة بيانات بسيطة
DB_FILE = 'nms_db.json'

def load_data():
    if not os.path.exists(DB_FILE):
        return {
            "users": {"admin": {"pass": "admin123", "role": "admin"}},
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],
            "tasks": {"start": ["Power On", "Uniform"], "end": ["Cleaned", "Power Off"], "marketing": ["WhatsApp"]}
        }
    with open(DB_FILE, 'r') as f:
        return json.load(f)

db = load_data()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 NMS Login")
    user = st.selectbox("User", list(db["users"].keys()))
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if db["users"][user]["pass"] == pwd:
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.rerun()
else:
    st.success(f"Welcome {st.session_state['user']}")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
    st.write("البرنامج يعمل الآن بنجاح! يمكنك إضافة باقي الجداول لاحقاً.")
