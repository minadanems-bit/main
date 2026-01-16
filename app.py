import streamlit as st
import pandas as pd
from datetime import datetime, date
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
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "salary": 0.0, "hiring_date": "2024-01-01", "bonus": [], "deductions": []},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "salary": 3000.0, "hiring_date": "2024-01-01", "bonus": [], "deductions": []}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "expense_categories": ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Other"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [],
            "drafts": {},
            "history": []
        }
    with open(DB_FILE, 'r') as f: 
        data = json.load(f)
        if "history" not in data: data["history"] = []
        if "expense_categories" not in data: data["expense_categories"] = ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Other"]
        # Ensure HR structure exists for old users
        for user in data["users"]:
            if "bonus" not in data["users"][user]: data["users"][user]["bonus"] = []
            if "deductions" not in data["users"][user]: data["users"][user]["deductions"] = []
            if "salary" not in data["users"][user]: data["users"][user]["salary"] = 0.0
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & Session Logic ---
st.set_page_config(page_title="NMS ERP - Enterprise Solution", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_', 'exp_'))}
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
                    for key, val in db["drafts"][u].items():
                        st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Authentication Failed")

else:
    # --- 4. Sidebar ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"Welcome, {db['users'][st.session_state['user']]['full_name']}")
        user_node = db["users"][st.session_state['user']]
        if user_node.get("photo"): st.image(base64.b64decode(user_node["photo"]), width=150)
        
        prof_pic = st.file_uploader("Change Photo", type=['jpg', 'png'])
        if st.button("Update Profile Photo"):
            if prof_pic:
                db["users"][st.session_state['user']]["photo"] = base64.b64encode(prof_pic.getvalue()).decode()
                save_db(db); st.success("Updated!"); st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Master Control")
            admin_mode = st.radio("Management Suite", ["Review History", "HR & Payroll", "Manage Employees", "Manage Expenses", "Manage Branches", "Audit Logs"])
            
            if admin_mode == "HR & Payroll":
                st.subheader("👥 Human Resources & Payroll Management")
                target_emp = st.selectbox("Select Employee to Manage", list(db["users"].keys()))
                emp_data = db["users"][target_emp]
                
                hr_tab1, hr_tab2, hr_tab3 = st.tabs(["💰 Salary Settings", "📈 Bonus & Deductions", "📋 Attendance Report"])
                
                with hr_tab1:
                    st.write(f"### Financial File: {emp_data['full_name']}")
                    col_hr1, col_hr2 = st.columns(2)
                    with col_hr1:
                        new_base = st.number_input("Base Salary (الراتب الأساسي)", value=float(emp_data.get('salary', 0)), step=100.0)
                        hiring_dt = st.date_input("Hiring Date", value=datetime.strptime(emp_data.get('hiring_date', "2024-01-01"), "%Y-%m-%d"))
                    with col_hr2:
                        # Calculation of Advance Payments from Expenses History
                        advances = sum([h['expenses'] for h in db['history'] if h['staff'] == target_emp and "Advance" in h.get('exp_note', '')])
                        st.info(f"Total Salary Advances: {advances:,.2f} LE")
                        
                    if st.button("Update Employee Contract"):
                        db["users"][target_emp]["salary"] = new_base
                        db["users"][target_emp]["hiring_date"] = str(hiring_dt)
                        save_db(db); st.success("Contract Updated")

                with hr_tab2:
                    st.write("### Rewards & Penalties")
                    col_tr1, col_tr2 = st.columns(2)
                    with col_tr1:
                        st.markdown("#### Add Bonus (مكافأة)")
                        b_amt = st.number_input("Bonus Amount", min_value=0.0, step=50.0, key="b_amt")
                        b_reason = st.text_input("Reason", key="b_res")
                        if st.button("➕ Grant Bonus"):
                            db["users"][target_emp]["bonus"].append({"date": str(date.today()), "amt": b_amt, "reason": b_reason})
                            save_db(db); st.success("Bonus Added")
                    with col_tr2:
                        st.markdown("#### Add Deduction (جزاء)")
                        d_amt = st.number_input("Deduction Amount", min_value=0.0, step=50.0, key="d_amt")
                        d_reason = st.text_input("Reason", key="d_res")
                        if st.button("➖ Apply Deduction"):
                            db["users"][target_emp]["deductions"].append({"date": str(date.today()), "amt": d_amt, "reason": d_reason})
                            save_db(db); st.warning("Deduction Applied")
                    
                    st.divider()
                    st.write("Current Month Activity")
                    b_df = pd.DataFrame(db["users"][target_emp]["bonus"])
                    d_df = pd.DataFrame(db["users"][target_emp]["deductions"])
                    st.write("Bonuses:", b_df if not b_df.empty else "No bonuses")
                    st.write("Deductions:", d_df if not d_df.empty else "No deductions")

                with hr_tab3:
                    st.write("### Performance & Attendance")
                    user_logs = [log for log in db["logs"] if log["user"] == target_emp and log["action"] == "Login"]
                    if user_logs:
                        log_df = pd.DataFrame(user_logs)
                        st.dataframe(log_df, use_container_width=True)
                    else:
                        st.info("No login logs found for this employee.")

            elif admin_mode == "Manage Expenses":
                st.subheader("💰 Manage Expense Categories")
                new_cat = st.text_input("New Expense Category Name")
                if st.button("➕ Add Category"):
                    if new_cat and new_cat not in db["expense_categories"]:
                        db["expense_categories"].append(new_cat)
                        save_db(db); st.success(f"Added: {new_cat}"); st.rerun()
                st.divider()
                cat_to_del = st.selectbox("Select Category to Delete", db["expense_categories"])
                if st.button("🗑️ Remove Category", type="primary"):
                    if len(db["expense_categories"]) > 1:
                        db["expense_categories"].remove(cat_to_del)
                        save_db(db); st.warning("Deleted!"); st.rerun()

            elif admin_mode == "Review History":
                st.subheader("📜 Shift Archive Explorer")
                if not db["history"]:
                    st.warning("No records found in history.")
                else:
                    hist_df = pd.DataFrame(db["history"])
                    search_date = st.date_input("Filter by Date", datetime.now())
                    search_branch = st.selectbox("Filter by Branch", ["All"] + db["branches"])
                    
                    filtered = hist_df[hist_df['date'] == str(search_date)]
                    if search_branch != "All":
                        filtered = filtered[filtered['branch'] == search_branch]
                    
                    if not filtered.empty:
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Total Sales", f"{filtered['sales'].sum():,.2f}")
                        m2.metric("Total Net Diff", f"{filtered['net_diff'].sum():,.2f}")
                        m3.metric("Opay Activity", f"{filtered['opay_move'].sum():,.2f}")
                        m4.metric("Shifts Count", len(filtered))
                        
                        st.divider()
                        for _, row in filtered.iterrows():
                            with st.expander(f"📄 Report: {row['staff']} | {row['branch']} | {row['shift']}"):
                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    st.markdown("### 💰 Financials")
                                    st.write(f"**Sales:** {row.get('sales', 0.0):,.2f}")
                                    st.write(f"**Act. Drawer:** {row.get('actual_cash', 0.0):,.2f}")
                                    diff = row.get('net_diff', 0.0)
                                    color = "green" if abs(diff) < 0.1 else "red"
                                    st.markdown(f"**Diff:** :{color}[{diff:,.2f}]")
                                with c2:
                                    st.markdown("### 🖨️ Printers")
                                    st.write(f"**Kyo Used:** {row.get('kyo_used', 0)}")
                                    st.write(f"**Xerox Used:** {row.get('xerox_used', 0)}")
                                with c3:
                                    st.markdown("### 📝 Tasks")
                                    st.write(f"**Exp Note:** {row.get('exp_note', 'N/A')}")
                                st.dataframe(pd.DataFrame([row]), hide_index=True)

            elif admin_mode == "Manage Employees":
                st.subheader("👥 Employee Master Control")
                with st.expander("➕ Register New Employee"):
                    new_u_name = st.text_input("Username (Login ID)")
                    new_u_pass = st.text_input("Set Password", type="password")
                    new_u_full = st.text_input("Full Name")
                    if st.button("Create Account"):
                        if new_u_name and new_u_name not in db["users"]:
                            db["users"][new_u_name] = {"pass": new_u_pass, "role": "user", "full_name": new_u_full, "salary": 0.0, "bonus": [], "deductions": []}
                            save_db(db); st.success(f"Account created!"); st.rerun()

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
            st.warning(f"📦 تنبيه هام: يوجد (Debit) مُرحل من الشفت السابق بقيمة: {db['pending_debit']:,.2f} جنيه.")
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
            opay_start = st.number_input("Opay Opening Balance", step=0.0001, format="%.4f", key="ops", on_change=sync_draft)
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
            st.write("**Closing Cash**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE  ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins  ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            
            st.divider()
            st.write("**Expenses (المصاريف)**")
            exp_cat = st.selectbox("Category", db["expense_categories"], key="exp_cat_sel", on_change=sync_draft)
            exp_val = st.number_input("Amount", step=1.0, key="c_exp", on_change=sync_draft)
            exp_note = st.text_input("Details", key="exp_note_text", on_change=sync_draft)
            full_exp_note = f"{exp_cat}: {exp_note}" if exp_note else exp_cat
            
            st.divider()
            expected_cash = t_open + sys_sales + u10_debit - exp_val - v22_debit - t_e_pay
            net_diff = t_close - expected_cash
            st.metric("Expected Cash (Drawer)", f"{expected_cash:,.2f} LE")
            if abs(net_diff) < 0.1: st.success("✅ Match")
            else: st.error(f"⚠️ Diff: {net_diff:,.2f}")

        with c3:
            st.write("**Systems & Printer Analysis**")
            opay_end = st.number_input("Opay Final Balance", step=0.0001, format="%.4f", key="op_end", on_change=sync_draft)
            opay_diff = opay_start - opay_end
            st.divider()
            st.markdown("#### Kyocera")
            k_end = st.number_input("K Counter End", step=1, key="k1end", on_change=sync_draft)
            k_actual = k_end - k_start
            st.write(f"K Used: {k_actual}")
            st.divider()
            st.markdown("#### Xerox")
            x_end = st.number_input("X Counter End", step=1, key="x2end", on_change=sync_draft)
            x_actual = x_end - x_start
            st.write(f"X Used: {x_actual}")

    with tab3:
        st.subheader("Social Media Tasks")
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["social"]): m_cols[i%4].checkbox(task, key=f"m_{task}", on_change=sync_draft)
        st.divider(); st.write("**Interaction**")
        i_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["interaction"]): i_cols[i%4].checkbox(task, key=f"i_{task}", on_change=sync_draft)

    # --- 6. Exporting ---
    st.divider()
    diff_status = "✅ Match" if abs(net_diff) < 0.1 else f"⚠️ {net_diff}"
    wa_msg = f"*🚀 NMS FULL REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n*💰 FINANCIALS:*\n- Sales: {sys_sales:,.2f}\n- Exp: {exp_val:,.2f} ({full_exp_note})\n- Drawer: {t_close:,.2f}\n- *Status:* {diff_status}\n\n*🖨️ PRINTERS:*\n- Kyo Used: {k_actual}\n- Xerox Used: {x_actual}"

    if st.button("🏁 SUBMIT & ARCHIVE FULL SHIFT DATA", use_container_width=True):
        archive_data = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.now().strftime('%H:%M:%S'),
            "staff": st.session_state['user'],
            "branch": branch,
            "shift": shift,
            "opening_cash": t_open,
            "sales": sys_sales,
            "expenses": exp_val,
            "exp_note": full_exp_note,
            "actual_cash": t_close,
            "net_diff": net_diff,
            "kyo_used": k_actual,
            "xerox_used": x_actual,
            "opay_move": opay_diff
        }
        db["history"].append(archive_data)
        db["pending_debit"] = v22_debit
        save_db(db); st.success("Shift Archived Successfully!")

    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD FULL PDF REPORT", use_container_width=True):
            buffer = io.BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet(); elements = []
            elements.append(Paragraph(f"NMS DAILY REPORT - {branch}", styles['Title']))
            data_f = [["Item", "Amount"], ["Sales", sys_sales], ["Expenses", exp_val], ["Actual Cash", t_close], ["Net Diff", net_diff]]
            t1 = Table(data_f, colWidths=[200, 100]); t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.indianred)]))
            elements.append(t1); doc.build(elements)
            st.download_button("💾 Save PDF Report", data=buffer.getvalue(), file_name=f"NMS_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf")
    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND FULL WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
