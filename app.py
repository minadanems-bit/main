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
            "logo": None,
            "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "HQ", "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار", "كهرباء ومياه", "إيجار"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [], "drafts": {}, "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        if "history" not in data: data["history"] = []
        if "exp_categories" not in data: data["exp_categories"] = ["نثريات", "مشتريات ورق", "صيانة"]
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & Session Logic ---
st.set_page_config(page_title="NMS Management System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_', 'exp_list'))}
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
                    for key, val in db["drafts"][u].items(): st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Authentication Failed")
else:
    # --- 4. Sidebar ---
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

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Master Control")
            admin_mode = st.radio("Settings", ["Review History", "Manage Employees", "Manage Branches", "Manage Tasks", "Expense Categories", "Audit Logs"])
            
            if admin_mode == "Review History":
                st.subheader("📜 Shift Archive Explorer")
                if not db["history"]: st.warning("No records found.")
                else:
                    hist_df = pd.DataFrame(db["history"])
                    search_date = st.date_input("Filter by Date", datetime.now())
                    search_branch = st.selectbox("Filter by Branch", ["All"] + db["branches"])
                    filtered = hist_df[hist_df['date'] == str(search_date)]
                    if search_branch != "All": filtered = filtered[filtered['branch'] == search_branch]
                    
                    if not filtered.empty:
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Total Sales", f"{filtered['sales'].sum():,.2f}")
                        m2.metric("Total Expenses", f"{filtered['expenses'].sum():,.2f}")
                        m3.metric("Net Diff", f"{filtered['net_diff'].sum():,.2f}")
                        m4.metric("Shifts", len(filtered))
                        for _, row in filtered.iterrows():
                            with st.expander(f"📄 Report: {row['staff']} | {row['branch']} | {row['shift']}"):
                                st.write(f"**Detailed Expenses:** {row.get('exp_details', 'None')}")
                                st.dataframe(pd.DataFrame([row]), hide_index=True)

            elif admin_mode == "Expense Categories":
                st.subheader("💰 Manage Expense Types")
                new_cat = st.text_input("New Expense Category Name")
                if st.button("Add Category"):
                    db["exp_categories"].append(new_cat); save_db(db); st.rerun()
                cat_to_del = st.selectbox("Delete Category", db["exp_categories"])
                if st.button("Remove Category"):
                    db["exp_categories"].remove(cat_to_del); save_db(db); st.rerun()

            elif admin_mode == "Manage Employees":
                st.subheader("👥 Employee Master Control")
                with st.expander("➕ Register New Employee"):
                    new_u_name = st.text_input("Username")
                    new_u_pass = st.text_input("Password", type="password")
                    if st.button("Create Account"):
                        db["users"][new_u_name] = {"pass": new_u_pass, "role": "user", "full_name": new_u_name}
                        save_db(db); st.success("Created!"); st.rerun()

            elif admin_mode == "Manage Branches":
                n_br = st.text_input("New Branch Name")
                if st.button("Add Branch"): db["branches"].append(n_br); save_db(db); st.rerun()

            elif admin_mode == "Manage Tasks":
                cat = st.selectbox("Category", ["Opening", "Closing", "Social"])
                new_t = st.text_input("Add Task")
                if st.button("➕ Add"): db["tasks"][cat.lower()].append(new_t); save_db(db); st.rerun()

            elif admin_mode == "Audit Logs": st.dataframe(pd.DataFrame(db["logs"]).tail(50))

    # --- 5. Main Dashboard ---
    st.title("📊 Daily Shift Control")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with inf2: st.info(f"🕒 **Day:** {datetime.now().strftime('%A')}")
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL MEDIA"])

    with tab1:
        st.subheader("Opening Procedures")
        if db.get("pending_debit", 0) > 0: st.warning(f"📦 تنبيه: يوجد (Debit) مُرحل: {db['pending_debit']:,.2f} جنيه.")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, format="%.2f", key="oc", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total Opening: {t_open:,.2f} LE**")
        with c3:
            k_start = st.number_input("Kyocera Opening", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Opening", step=1, key="xs", on_change=sync_draft)
            opay_start = st.number_input("Opay Start", step=0.01, format="%.4f", key="ops", on_change=sync_draft)
            u10_debit = st.number_input("Debit Received", min_value=0.0, step=1.0, key="u10_val", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            sys_sales = st.number_input("System Sales", min_value=0.0, step=1.0, key="c_sys_sales", on_change=sync_draft)
            v22_debit = st.number_input("Debit Pending", min_value=0.0, step=1.0, key="v22_val", on_change=sync_draft)
            instapay = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1.0, key="c_visa", on_change=sync_draft)
            t_e_pay = instapay + wallet + visa
        with c2:
            st.write("**Expense Tracker**")
            if 'exp_list' not in st.session_state: st.session_state.exp_list = []
            exp_col1, exp_col2 = st.columns([1, 1])
            with exp_col1: exp_type = st.selectbox("Category", db["exp_categories"])
            with exp_col2: exp_amt = st.number_input("Amount", min_value=0.0, step=1.0)
            exp_desc = st.text_input("Details (e.g., 2 Reams of paper)")
            if st.button("➕ Add Expense"):
                st.session_state.exp_list.append({"type": exp_type, "amount": exp_amt, "desc": exp_desc})
                sync_draft(); st.rerun()
            
            expenses = 0.0
            if st.session_state.exp_list:
                df_exp = pd.DataFrame(st.session_state.exp_list)
                st.table(df_exp)
                expenses = df_exp['amount'].sum()
                if st.button("Clear All Expenses"): st.session_state.exp_list = []; st.rerun()

            st.divider()
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE  ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins  ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            expected_cash = t_open + sys_sales + u10_debit - expenses - v22_debit - t_e_pay
            net_diff = t_close - expected_cash
            st.metric("Expected Drawer", f"{expected_cash:,.2f} LE")
            if abs(net_diff) < 0.1: st.success("✅ Match")
            else: st.error(f"⚠️ Diff: {net_diff:,.2f}")

        with c3:
            opay_end = st.number_input("Opay End", step=0.01, format="%.4f", key="op_end", on_change=sync_draft)
            opay_diff = opay_start - opay_end
            st.markdown("### 🖨️ Kyocera")
            k_end = st.number_input("Counter End", step=1, key="k1end", on_change=sync_draft); k_actual = k_end - k_start
            st.write(f"Used: {k_actual}")
            st.markdown("### 🖨️ Xerox")
            x_end = st.number_input("Counter End (X)", step=1, key="x2end", on_change=sync_draft); x_actual = x_end - x_start
            st.write(f"Used: {x_actual}")

    with tab3:
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["social"]): m_cols[i%4].checkbox(task, key=f"m_{task}", on_change=sync_draft)

    st.divider()
    exp_summary = ", ".join([f"{x['type']}({x['amount']})" for x in st.session_state.exp_list])
    wa_msg = f"*🚀 NMS REPORT*\n*Staff:* {st.session_state['user']}\n- Sales: {sys_sales}\n- Exp: {expenses} [{exp_summary}]\n- Drawer: {t_close}\n- Diff: {net_diff}"

    if st.button("🏁 SUBMIT & ARCHIVE FULL SHIFT DATA", use_container_width=True):
        archive_data = {
            "date": datetime.now().strftime('%Y-%m-%d'), "staff": st.session_state['user'], "branch": branch, "shift": shift,
            "sales": sys_sales, "expenses": expenses, "exp_details": exp_summary, "actual_cash": t_close, "net_diff": net_diff, "opay_move": opay_diff,
            "kyo_used": k_actual, "xerox_used": x_actual
        }
        db["history"].append(archive_data); db["pending_debit"] = v22_debit; db["drafts"][st.session_state['user']] = {}
        save_db(db); st.success("Archived!"); st.session_state.exp_list = []; st.rerun()

    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD PDF", use_container_width=True):
            buffer = io.BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=letter); styles = getSampleStyleSheet(); elements = []
            elements.append(Paragraph(f"NMS Report - {branch}", styles['Title']))
            elements.append(Paragraph(f"Expenses: {exp_summary}", styles['Normal']))
            doc.build(elements)
            st.download_button("💾 Save PDF", data=buffer.getvalue(), file_name=f"NMS_{datetime.now().strftime('%Y%m%d')}.pdf")
    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; font-weight:bold;">📱 WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
