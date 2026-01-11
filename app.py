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
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار", "كهرباء ومياه"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform", "Music On", "Paper Loaded", "Cash Counted"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint"],
                "social": ["WhatsApp Story", "Facebook Post", "Instagram Reel", "TikTok"],
                "interaction": ["Like", "Share", "Comment"]
            },
            "logs": [], "drafts": {}, "history": [], "payroll_history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        # Ensure new keys exist for old users
        for u in data["users"]:
            for key in ["salary", "advances", "deductions", "bonus", "off_days"]:
                if key not in data["users"][u]: data["users"][u][key] = 0
        if "payroll_history" not in data: data["payroll_history"] = []
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & Session Logic ---
st.set_page_config(page_title="NMS Management System", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})
if 'exp_list' not in st.session_state:
    st.session_state.exp_list = []

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_'))}
        current_data['exp_list'] = st.session_state.exp_list
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
                    draft = db["drafts"][u]
                    for key, val in draft.items():
                        if key == 'exp_list': st.session_state.exp_list = val
                        else: st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Authentication Failed")

else:
    # --- 4. Sidebar ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"User: {st.session_state['user']}")
        user_node = db["users"][st.session_state['user']]
        
        # Financial Summary for Employee
        if st.session_state['role'] != 'admin':
            st.info(f"💰 **Salary Status:**\n- Basic: {user_node.get('salary', 0)}\n- Advances: {user_node.get('advances', 0)}\n- Deductions: {user_node.get('deductions', 0)}\n- Bonus: {user_node.get('bonus', 0)}")

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
            admin_mode = st.radio("Settings", ["Payroll Management", "Review History", "Manage Employees", "Manage Branches", "Manage Tasks", "Expense Categories", "Audit Logs"])
            
            if admin_mode == "Payroll Management":
                st.subheader("💳 Salary & Payroll Center")
                emp = st.selectbox("Select Employee", [u for u in db["users"].keys() if db["users"][u]['role'] != 'admin'])
                u_data = db["users"][emp]
                
                c1, c2 = st.columns(2)
                with c1:
                    new_sal = st.number_input("Basic Salary", value=float(u_data.get('salary', 0)))
                    add_adv = st.number_input("Add Advance (سلفة)", min_value=0.0)
                    add_ded = st.number_input("Add Deduction (خصم)", min_value=0.0)
                with c2:
                    add_bon = st.number_input("Add Bonus (حافز)", min_value=0.0)
                    add_off = st.number_input("Add Off Days (إجازات)", min_value=0)
                    if st.button("Apply Financial Changes"):
                        db["users"][emp]["salary"] = new_sal
                        db["users"][emp]["advances"] += add_adv
                        db["users"][emp]["deductions"] += add_ded
                        db["users"][emp]["bonus"] += add_bon
                        db["users"][emp]["off_days"] += add_off
                        save_db(db); st.success("Updated!"); st.rerun()
                
                st.divider()
                net_sal = u_data['salary'] + u_data['bonus'] - u_data['advances'] - u_data['deductions']
                st.metric(f"Current Net for {emp}", f"{net_sal:,.2f} LE")
                
                if st.button(f"🔴 CLOSE MONTH & RESET FOR {emp}", use_container_width=True):
                    payroll_record = {"date": datetime.now().strftime("%Y-%m"), "employee": emp, "net": net_sal, "details": f"Sal:{u_data['salary']}, Adv:{u_data['advances']}, Ded:{u_data['deductions']}, Bon:{u_data['bonus']}"}
                    db["payroll_history"].append(payroll_record)
                    # Reset
                    db["users"][emp].update({"advances": 0, "deductions": 0, "bonus": 0, "off_days": 0})
                    save_db(db); st.success("Month closed and balances reset!"); st.rerun()

            elif admin_mode == "Review History":
                st.subheader("📜 Shift Archive Explorer")
                if not db["history"]: st.warning("No records found.")
                else:
                    hist_df = pd.DataFrame(db["history"])
                    search_date = st.date_input("Filter by Date", datetime.now())
                    search_branch = st.selectbox("Filter by Branch", ["All"] + db["branches"])
                    filtered = hist_df[hist_df['date'] == str(search_date)]
                    if search_branch != "All": filtered = filtered[filtered['branch'] == search_branch]
                    if not filtered.empty:
                        for _, row in filtered.iterrows():
                            with st.expander(f"📄 Report: {row['staff']} | {row['branch']} | {row['shift']}"):
                                st.write(f"**Detailed Expenses:** {row.get('exp_details', 'N/A')}")
                                st.dataframe(pd.DataFrame([row]), hide_index=True)

            elif admin_mode == "Expense Categories":
                st.subheader("💰 Manage Expense Types")
                new_cat = st.text_input("New Category Name")
                if st.button("Add Category"):
                    db["exp_categories"].append(new_cat); save_db(db); st.rerun()
                cat_del = st.selectbox("Delete Category", db["exp_categories"])
                if st.button("Remove Category"):
                    db["exp_categories"].remove(cat_del); save_db(db); st.rerun()

            elif admin_mode == "Manage Employees":
                st.subheader("👥 Employee Master Control")
                with st.expander("➕ Register New Employee"):
                    new_u_name = st.text_input("Username")
                    new_u_pass = st.text_input("Password", type="password")
                    if st.button("Create Account"):
                        db["users"][new_u_name] = {"pass": new_u_pass, "role": "user", "full_name": new_u_name, "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0}
                        save_db(db); st.rerun()

            elif admin_mode == "Manage Branches":
                st.subheader("🏢 Branch Management")
                n_br = st.text_input("New Branch Name")
                if st.button("Add Branch"): db["branches"].append(n_br); save_db(db); st.rerun()

            elif admin_mode == "Manage Tasks":
                st.subheader("📝 Task Management")
                cat = st.selectbox("Category", ["Opening", "Closing", "Social"])
                new_t = st.text_input("Add Task")
                if st.button("➕ Add"): db["tasks"][cat.lower()].append(new_t); save_db(db); st.rerun()

            elif admin_mode == "Audit Logs":
                st.dataframe(pd.DataFrame(db["logs"]).tail(50))

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
        if db.get("pending_debit", 0) > 0:
            st.warning(f"📦 تنبيه هام: يوجد (Debit) مُرحل بقيمة: {db['pending_debit']:,.2f} جنيه.")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Opening Checklist**")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, format="%.2f", key="oc", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total Opening: {t_open:,.2f} LE**")
        with c3:
            st.write("**Start Counters & Debit In**")
            k_start = st.number_input("Kyocera Opening", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Opening", step=1, key="xs", on_change=sync_draft)
            opay_start = st.number_input("Opay Opening Balance", step=0.01, format="%.4f", key="ops", on_change=sync_draft)
            u10_debit = st.number_input("Debit Received", min_value=0.0, step=1.0, key="u10_val", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.write("**Financial Input**")
            sys_sales = st.number_input("System Sales", min_value=0.0, step=1.0, key="c_sys_sales", on_change=sync_draft)
            v22_debit = st.number_input("Debit Pending", min_value=0.0, step=1.0, key="v22_val", on_change=sync_draft)
            instapay = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1.0, key="c_visa", on_change=sync_draft)
            t_e_pay = instapay + wallet + visa
        with c2:
            st.write("**Expense Tracker**")
            exp_col1, exp_col2 = st.columns([1, 1])
            with exp_col1: e_type = st.selectbox("Category", db["exp_categories"])
            with exp_col2: e_amt = st.number_input("Amount", min_value=0.0, key="cur_exp_amt")
            e_desc = st.text_input("Details / Reason", key="cur_exp_desc")
            if st.button("➕ Add Expense Item"):
                st.session_state.exp_list.append({"Type": e_type, "Amount": e_amt, "Details": e_desc})
                sync_draft(); st.rerun()
            expenses = 0.0
            if st.session_state.exp_list:
                df_exp = pd.DataFrame(st.session_state.exp_list)
                st.dataframe(df_exp, use_container_width=True, hide_index=True)
                expenses = df_exp['Amount'].sum()
                if st.button("🗑️ Clear Expenses"): st.session_state.exp_list = []; sync_draft(); st.rerun()
            st.divider()
            st.write("**Closing Cash**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            expected_cash = t_open + sys_sales + u10_debit - expenses - v22_debit - t_e_pay
            net_diff = t_close - expected_cash
            st.metric("Expected Cash", f"{expected_cash:,.2f} LE")
            if abs(net_diff) < 0.1: st.success("✅ Match")
            else: st.error(f"⚠️ Diff: {net_diff:,.2f}")
        with c3:
            st.write("**Printer Analysis**")
            opay_end = st.number_input("Opay Final", step=0.01, format="%.4f", key="op_end", on_change=sync_draft)
            opay_diff = opay_start - opay_end
            st.divider()
            k_end = st.number_input("Kyocera End", step=1, key="k1end", on_change=sync_draft)
            k_actual = k_end - k_start
            st.write(f"Kyo Used: {k_actual}")
            st.divider()
            x_end = st.number_input("Xerox End", step=1, key="x2end", on_change=sync_draft)
            x_actual = x_end - x_start
            st.write(f"Xerox Used: {x_actual}")

    with tab3:
        st.subheader("Social Media Tasks")
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["social"]): m_cols[i%4].checkbox(task, key=f"m_{task}", on_change=sync_draft)
        st.divider(); st.write("**Interaction**")
        i_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["interaction"]): i_cols[i%4].checkbox(task, key=f"i_{task}", on_change=sync_draft)

    # --- 6. Exporting ---
    st.divider()
    exp_details_str = ", ".join([f"{x['Type']}:{x['Amount']}" for x in st.session_state.exp_list])
    diff_status = "✅ Match" if abs(net_diff) < 0.1 else f"⚠️ {net_diff}"
    wa_msg = f"*🚀 NMS REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n*Sales:* {sys_sales}\n*Expenses:* {expenses} ({exp_details_str})\n*Drawer:* {t_close}\n*Diff:* {diff_status}"

    if st.button("🏁 SUBMIT & ARCHIVE FULL SHIFT DATA", use_container_width=True):
        archive_data = {"date": datetime.now().strftime('%Y-%m-%d'), "staff": st.session_state['user'], "branch": branch, "sales": sys_sales, "expenses": expenses, "exp_details": exp_details_str, "net_diff": net_diff, "kyo_used": k_actual, "xerox_used": x_actual}
        db["history"].append(archive_data); db["pending_debit"] = v22_debit
        db["drafts"][st.session_state['user']] = {}; st.session_state.exp_list = []
        save_db(db); st.success("Archived!"); st.rerun()

    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD PDF REPORT", use_container_width=True):
            buffer = io.BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=letter); elements = []
            elements.append(Paragraph(f"NMS REPORT - {branch}", getSampleStyleSheet()['Title']))
            elements.append(Table([["Item", "Value"], ["Sales", sys_sales], ["Expenses", expenses], ["Drawer", t_close]], colWidths=[200, 100]))
            doc.build(elements)
            st.download_button("💾 Save PDF", data=buffer.getvalue(), file_name="report.pdf")
    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer;">📱 SEND WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
