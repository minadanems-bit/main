{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
from datetime import datetime\
import json\
import os\
from reportlab.lib import colors\
from reportlab.lib.pagesizes import letter\
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer\
from reportlab.lib.styles import getSampleStyleSheet\
import io\
\
# \uc0\u1578 \u1601 \u1593 \u1610 \u1604  \u1582 \u1575 \u1589 \u1610 \u1577  \u1575 \u1604 \u1573 \u1583 \u1582 \u1575 \u1604  \u1576 \u1575 \u1604 \u1603 \u1610 \u1576 \u1608 \u1585 \u1583  \u1576 \u1588 \u1603 \u1604  \u1571 \u1587 \u1585 \u1593 \
st.set_page_config(page_title="NMS Shift System", layout="wide")\
\
DB_FILE = 'nms_db.json'\
\
def load_data():\
    if not os.path.exists(DB_FILE):\
        default_data = \{\
            "users": \{\
                "admin": \{"pass": "admin123", "role": "admin"\},\
                "Mina": \{"pass": "1234", "role": "user"\},\
                "Youstina": \{"pass": "1234", "role": "user"\},\
                "Mark": \{"pass": "1234", "role": "user"\},\
                "Fatma": \{"pass": "1234", "role": "user"\}\
            \},\
            "branches": ["Mouhamed Nagib branch", "El Tram branch"],\
            "tasks": \{\
                "start": ["Finger Print", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],\
                "end": ["Contacts", "Place Cleaned", "Power Off", "Cash Counted", "Finger Print", "Report Sent"],\
                "marketing": ["Canva 1", "Canva 2", "WhatsApp Story", "FB Story", "TikTok Post", "Instagram Reel"]\
            \}\
        \}\
        with open(DB_FILE, 'w') as f:\
            json.dump(default_data, f)\
        return default_data\
    with open(DB_FILE, 'r') as f:\
        return json.load(f)\
\
def save_data(data):\
    with open(DB_FILE, 'w') as f:\
        json.dump(data, f)\
\
db = load_data()\
\
if 'logged_in' not in st.session_state:\
    st.session_state['logged_in'] = False\
\
# --- \uc0\u1578 \u1591 \u1576 \u1610 \u1602  \u1575 \u1604 \u1608 \u1575 \u1580 \u1607 \u1577  ---\
if not st.session_state['logged_in']:\
    st.title("\uc0\u55357 \u56592  NMS System Login")\
    user = st.selectbox("Employee", list(db["users"].keys()))\
    pwd = st.text_input("Password", type="password")\
    if st.button("Login"):\
        if db["users"][user]["pass"] == pwd:\
            st.session_state['logged_in'] = True\
            st.session_state['user'] = user\
            st.session_state['role'] = db["users"][user]["role"]\
            st.rerun()\
else:\
    # \uc0\u1575 \u1604 \u1602 \u1575 \u1574 \u1605 \u1577  \u1575 \u1604 \u1580 \u1575 \u1606 \u1576 \u1610 \u1577 \
    with st.sidebar:\
        st.write(f"Logged in as: **\{st.session_state['user']\}**")\
        if st.button("Logout"):\
            st.session_state['logged_in'] = False\
            st.rerun()\
        \
        if st.session_state['role'] == 'admin':\
            st.divider()\
            st.subheader("\uc0\u9881 \u65039  Admin Tools")\
            new_u = st.text_input("Employee Name")\
            new_p = st.text_input("Password")\
            if st.button("Add/Update Employee"):\
                db["users"][new_u] = \{"pass": new_p, "role": "user"\}\
                save_data(db)\
                st.success("Saved!")\
\
    # \uc0\u1575 \u1604 \u1605 \u1593 \u1604 \u1608 \u1605 \u1575 \u1578  \u1575 \u1604 \u1571 \u1587 \u1575 \u1587 \u1610 \u1577 \
    c1, c2, c3 = st.columns(3)\
    with c1: st.info(f"\uc0\u55357 \u56517  \{datetime.now().strftime('%Y-%m-%d (%A)')\}")\
    with c2: branch = st.selectbox("Branch", db["branches"])\
    with c3: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])\
\
    tab1, tab2, tab3 = st.tabs(["\uc0\u55357 \u57314  Start Shift", "\u55357 \u56628  End Shift", "\u55357 \u56561  Marketing"])\
\
    with tab1:\
        col_chk, col_cash, col_pr = st.columns([1, 1, 1])\
        with col_chk:\
            st.subheader("Checklist")\
            s_tasks = [st.checkbox(t, key=f"s_\{t\}") for t in db["tasks"]["start"]]\
        \
        with col_cash:\
            st.subheader("\uc0\u55357 \u56496  Opening Cash")\
            # \uc0\u1575 \u1587 \u1578 \u1582 \u1583 \u1575 \u1605  step=1 \u1608  format="%d" \u1610 \u1580 \u1593 \u1604  \u1575 \u1604 \u1573 \u1583 \u1582 \u1575 \u1604  \u1576 \u1575 \u1604 \u1603 \u1610 \u1576 \u1608 \u1585 \u1583  \u1605 \u1605 \u1578 \u1575 \u1586 \u1575 \u1611 \
            o200 = st.number_input("200 LE", step=1, value=0, format="%d")\
            o100 = st.number_input("100 LE", step=1, value=0, format="%d")\
            o50 = st.number_input("50 LE", step=1, value=0, format="%d")\
            o20 = st.number_input("20 LE", step=1, value=0, format="%d")\
            o10 = st.number_input("10 LE", step=1, value=0, format="%d")\
            o5 = st.number_input("5 LE", step=1, value=0, format="%d")\
            o_coins = st.number_input("Coins", step=1, value=0, format="%d")\
            total_open = (o200*200)+(o100*100)+(o50*50)+(o20*20)+(o10*10)+(o5*5)+o_coins\
            st.metric("Total Opening", f"\{total_open\} LE")\
\
        with col_pr:\
            st.subheader("\uc0\u55357 \u56744 \u65039  Initial Counters")\
            k_start = st.number_input("Kyocera Start", step=1, value=0, format="%d")\
            x_start = st.number_input("Xerox Start", step=1, value=0, format="%d")\
            opay_start = st.number_input("Opay Start Balance", step=1, value=0, format="%d")\
\
    with tab2:\
        col_chk2, col_cash2, col_pr2 = st.columns([1, 1, 1])\
        with col_chk2:\
            st.subheader("Checklist")\
            e_tasks = [st.checkbox(t, key=f"e_\{t\}") for t in db["tasks"]["end"]]\
\
        with col_cash2:\
            st.subheader("\uc0\u55357 \u56496  Closing Cash")\
            c200 = st.number_input("200 LE ", step=1, value=0, format="%d")\
            c100 = st.number_input("100 LE ", step=1, value=0, format="%d")\
            c50 = st.number_input("50 LE ", step=1, value=0, format="%d")\
            c20 = st.number_input("20 LE ", step=1, value=0, format="%d")\
            c10 = st.number_input("10 LE ", step=1, value=0, format="%d")\
            c5 = st.number_input("5 LE ", step=1, value=0, format="%d")\
            c_coins = st.number_input("Coins ", step=1, value=0, format="%d")\
            exp = st.number_input("Expenses (\uc0\u1575 \u1604 \u1605 \u1589 \u1575 \u1585 \u1610 \u1601 )", step=1, value=0, format="%d")\
            \
            total_close = (c200*200)+(c100*100)+(c50*50)+(c20*20)+(c10*10)+(c5*5)+c_coins\
            net_diff = (total_close + exp) - total_open\
            st.metric("Net Difference", f"\{net_diff\} LE")\
\
        with col_pr2:\
            st.subheader("\uc0\u55357 \u56522  Final Usage")\
            k_end = st.number_input("Kyocera End", step=1, value=0, format="%d")\
            x_end = st.number_input("Xerox End", step=1, value=0, format="%d")\
            st.write(f"Kyocera Diff: \{k_end - k_start\}")\
            st.write(f"Xerox Diff: \{x_end - x_start\}")\
            \
            st.divider()\
            one_s = st.number_input("One Side Count", step=1, value=0, format="%d")\
            duplex = st.number_input("Duplex Count", step=1, value=0, format="%d")\
            \
            st.divider()\
            st.write("Non-Cash")\
            visa = st.number_input("Visa", step=1, value=0, format="%d")\
            instapay = st.number_input("Instapay", step=1, value=0, format="%d")\
\
    with tab3:\
        st.subheader("Marketing Checklist")\
        m_tasks = [st.checkbox(t, key=f"m_\{t\}") for t in db["tasks"]["marketing"]]\
\
    if st.button("Generate Final Report & PDF", type="primary"):\
        st.success("Report Ready for Download!")\
        # \uc0\u1605 \u1604 \u1575 \u1581 \u1592 \u1577 : \u1603 \u1608 \u1583  \u1575 \u1604 \u1600  PDF \u1610 \u1592 \u1604  \u1603 \u1605 \u1575  \u1607 \u1608  \u1601 \u1610  \u1575 \u1604 \u1606 \u1587 \u1582 \u1577  \u1575 \u1604 \u1587 \u1575 \u1576 \u1602 \u1577 }