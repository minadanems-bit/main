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
            "logo": None, "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0, "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0, "photo": None}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "exp_categories": ["نثريات", "مشتريات ورق", "صيانة", "أحبار", "كهرباء ومياه"],
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
        # ضمان وجود حقول الرواتب للموظفين
        for u in data["users"]:
            for key in ["salary", "advances", "deductions", "bonus", "off_days"]:
                if key not in data["users"][u]: data["users"][u][key] = 0
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
        
        # عرض البيانات المالية للموظف في السايدبار
        if st.session_state['role'] != 'admin':
            st.divider()
            st.markdown("### 💰 My Wallet")
            net_salary = user_node['salary'] + user_node['bonus'] - user_node['advances'] - user_node['deductions']
            st.write(f"Basic: **{user_node['salary']}**")
            st.write(f"Net Balance: **{net_salary:,.2f} LE**")

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
            admin_mode = st.radio("Settings", ["Payroll & Salaries", "Review History", "Manage Employees", "Manage Branches", "Manage Tasks", "Expense Categories", "Audit Logs"])
            
            if admin_mode == "Payroll & Salaries":
                st.subheader("💳 Monthly Payroll Center")
                emp = st.selectbox("Select Employee", [u for u in db["users"].keys() if u != 'admin'])
                u_fin = db["users"][emp]
                c1, c2 = st.columns(2)
                with c1:
                    db["users"][emp]["salary"] = st.number_input("Monthly Salary", value=float(u_fin['salary']))
                    adv = st.number_input("Add Advance (سلفة)", 0.0)
                    ded = st.number_input("Add Deduction (خصم)", 0.0)
                with c2:
                    bon = st.number_input("Add Bonus (حافز)", 0.0)
                    off = st.number_input("Off Days", 0)
                    if st.button("Apply Financial Update"):
                        db["users"][emp]["advances"] += adv
                        db["users"][emp]["deductions"] += ded
                        db["users"][emp]["bonus"] += bon
                        db["users"][emp]["off_days"] += off
                        save_db(db); st.success("Updated Successfully!"); st.rerun()
                
                net = u_fin['salary'] + u_fin['bonus'] - u_fin['advances'] - u_fin['deductions']
                st.metric(f"Net for {emp}", f"{net:,.2f} LE")
                
                # --- PDF Generator for Salary Slip ---
                buf = io.BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=letter)
                parts = [Paragraph(f"Salary Report: {emp} - {datetime.now().strftime('%B %Y')}", getSampleStyleSheet()['Title'])]
                t_data = [["Description", "Amount"], ["Basic Salary", u_fin['salary']], ["Bonus (+)", u_fin['bonus']], ["Advances (-)", u_fin['advances']], ["Deductions (-)", u_fin['deductions']], ["Total Net", net]]
                tbl = Table(t_data, colWidths=[200, 100])
                tbl.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke)]))
                parts.append(tbl)
                doc.build(parts)
                st.download_button(f"📥 Download PDF Slip ({emp})", buf.getvalue(), f"Salary_{emp}.pdf")

                if st.button("🔴 RESET MONTH (Clear Balances)"):
                    db["users"][emp].update({"advances": 0, "deductions": 0, "bonus": 0, "off_days": 0})
                    save_db(db); st.warning("Balances cleared for new month."); st.rerun()

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

            elif admin_mode == "Manage Employees":
                st.subheader("👥 Employee Master Control")
                with st.expander("➕ Register New Employee"):
                    new_u_name = st.text_input("Username")
                    new_u_pass = st.text_input("Password", type="password")
                    if st.button("Create Account"):
                        db["users"][new_u_name] = {"pass": new_u_pass, "role": "user", "salary": 0, "advances": 0, "deductions": 0, "bonus": 0, "off_days": 0}
                        save_db(db); st.success("Created!"); st.rerun()
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                if st.button("Delete Employee") and target != 'admin':
                    del db["users"][target]; save_db(db); st.rerun()

            elif admin_mode == "Manage Branches":
                st.subheader("🏢 Branch Management")
                n_br = st.text_input("New Branch Name")
                if st.button("Add Branch"): db["branches"].append(n_br); save_db(db); st.rerun()
                rem_br = st.selectbox("Delete Branch", db["branches"])
                if st.button("Remove"): db["branches"].remove(rem_br); save_db(db); st.rerun()

            elif admin_mode == "Manage Tasks":
                st.subheader("📝 Task Management")
                cat = st.selectbox("Category", ["Opening", "Closing", "Social"])
                new_t = st.text_input("Add Task")
                if st.button("➕ Add"): db["tasks"][cat.lower()].append(new_t); save_db(db); st.rerun()

            elif admin_mode == "Expense Categories":
                st.subheader("💰 Manage Expense Types")
                new_cat = st.text_input("New Category Name")
                if st.button("Add Category"):
                    db["exp_categories"].append(new_cat); save_db(db); st.rerun()

    # --- 5. Main Dashboard (الأصلي بدون تغيير) ---
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
            o_coins = st.number_input("Coins (Decimal)", step=0.5, format="%.2f", key="oc", on_change=sync_draft)
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
            with exp_col2: e_amt = st.number_input("Amount", min_value=0.0, step=1.0, key="cur_exp_amt")
            e_desc = st.text_input("Details / Reason", key="cur_exp_desc")
            if st.button("➕ Add Expense Item"):
                st.session_state.exp_list.append({"Type": e_type, "Amount": e_amt, "Details": e_desc})
                sync_draft(); st.rerun()
            expenses = sum(x['Amount'] for x in st.session_state.exp_list)
            if st.session_state.exp_list:
                st.dataframe(pd.DataFrame(st.session_state.exp_list), use_container_width=True, hide_index=True)
            st.divider()
            st.write("**Closing Cash**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE  ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins  ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            expected_cash = t_open + sys_sales + u10_debit - expenses - v22_debit - t_e_pay
            net_diff = t_close - expected_cash
            st.metric("Expected Cash", f"{expected_cash:,.2f}", delta=f"{net_diff:,.2f}")

        with c3:
            st.write("**Systems & Printer Analysis**")
            opay_end = st.number_input("Opay Final Balance", step=0.01, format="%.4f", key="op_end", on_change=sync_draft)
            st.divider()
            st.markdown("### 🖨️ Kyocera")
            k_end = st.number_input("Counter End", step=1, key="k1end", on_change=sync_draft)
            k_os, k_dp, k_err, k_test = st.number_input("One-Side", 0, key="k1os"), st.number_input("Duplex", 0, key="k1dp"), st.number_input("Errors", 0, key="k1err"), st.number_input("Test", 0, key="k1tst")
            k_actual = k_end - k_start
            st.write(f"Used: {k_actual}")
            st.divider()
            st.markdown("### 🖨️ Xerox")
            x_end = st.number_input("Counter End (X)", step=1, key="x2end", on_change=sync_draft)
            x_os, x_dp, x_err, x_test = st.number_input("One-Side (X)", 0, key="x2os"), st.number_input("Duplex (X)", 0, key="x2dp"), st.number_input("Errors (X)", 0, key="x2err"), st.number_input("Test (X)", 0, key="x2tst")
            x_actual = x_end - x_start
            st.write(f"Used: {x_actual}")

    with tab3:
        st.subheader("Social Media Tasks")
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["social"]): m_cols[i%4].checkbox(task, key=f"m_{task}", on_change=sync_draft)

    # --- 6. Exporting ---
    st.divider()
    if st.button("🏁 SUBMIT & ARCHIVE FULL SHIFT DATA", use_container_width=True):
        archive_data = {"date": datetime.now().strftime('%Y-%m-%d'), "staff": st.session_state['user'], "branch": branch, "sales": sys_sales, "net_diff": net_diff}
        db["history"].append(archive_data); db["pending_debit"] = v22_debit
        db["drafts"][st.session_state['user']] = {}; st.session_state.exp_list = []
        save_db(db); st.success("Shift Archived!"); st.rerun()

    wa_msg = f"*NMS REPORT*\nStaff: {st.session_state['user']}\nSales: {sys_sales}\nDiff: {net_diff}"
    wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer;">📱 SEND WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
