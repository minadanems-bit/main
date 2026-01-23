import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
import io
import base64
import urllib.parse

from database import load_db, save_db, MANAGER_PHONE
from pdf_generator import create_downloadable_pdf

# Load database
db = load_db()

# Streamlit page setup
st.set_page_config(page_title="NMS ERP Platinum", layout="wide", page_icon="🚀")

# Session state setup
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

# Sync draft data
def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        draft_keys = (
            's_','o_','e_','c_','m_','i_','ks','xs','op',
            'u10','v22','ex','kj','xj','dn','k1','k2','x1','x2'
        )
        draft_data = {
            k: v for k, v in st.session_state.items() if k.startswith(draft_keys)
        }
        if "drafts" not in db:
            db["drafts"] = {}
        db["drafts"][user] = draft_data
        save_db(db)

# Login interface
if not st.session_state['logged_in']:
    st.title("🔐 NMS Enterprise Login")
    c1, c2 = st.columns(2)

    with c1:
        if db.get("logo"):
            st.image(base64.b64decode(db["logo"]), width=350)
        else:
            st.info("Upload Company Logo in Admin Panel")

    with c2:
        st.write("### Login")
        u = st.selectbox("Select Account", list(db["users"].keys()))
        p = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({
                    'logged_in': True,
                    'user': u,
                    'role': db["users"][u]["role"]
                })

                # Load draft data if exists
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items():
                        st.session_state[key] = val

                # Save login log
                db["logs"].append({
                    "user": u,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "Login"
                })
                save_db(db)
                st.rerun()
            else:
                st.error("Incorrect Password")

# Role-based redirection (after login)
else:
    if st.session_state['role'] == "admin":
        st.switch_page("1_Admin View")
    else:
        st.switch_page("2_User View")
