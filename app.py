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
                        m2.metric("Total Net Diff", f"{filtered['net_diff'].sum():,.2f}")
                        m3.metric("Opay Activity", f"{filtered['opay_move'].sum():,.2f}")
                        m4.metric("Shifts Count", len(filtered))
                        
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
                    new_u_name = st.text_input("Username (Login ID)")
                    new_u_pass = st.text_input("Set Password", type="password")
                    new_u_full = st.text_input("Full Name")
                    if st.button("Create Account"):
                        db["users"][new_u_name] = {"pass": new_u_pass, "role": "user", "full_name": new_u_full}
                        save_db(db); st.success(f"Account for {new_u_name} created!"); st.rerun()
                target_user = st.selectbox("Select Employee", list(db["users"].keys()))
                db["users"][target_user]["full_name"] = st.text_input("Full Name", db["users"][target_user].get("full_name", ""))
                db["users"][target_user]["pass"] = st.text_input("Password", db["users"][target_user]["pass"])
                if st.button("💾 Save Changes"): save_db(db); st.success("Updated!")

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
                v = st.number_input(f"{d} LE  ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins  ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            
            expected_cash = t_open + sys_sales + u10_debit - expenses - v22_debit - t_e_pay
            net_diff = t_close - expected_cash
            st.metric("Expected Cash (Drawer)", f"{expected_cash:,.2f} LE")
            if abs(net_diff) < 0.1: st.success("✅ Match")
            elif net_diff > 0: st.warning(f"➕ Surplus: {net_diff:,.2f}")
            else: st.error(f"➖ Shortage: {net_diff:,.2f}")

        with c3:
            st.write("**Systems & Printer Analysis**")
            opay_end = st.number_input("Opay Final Balance", step=0.01, format="%.4f", key="op_end", on_change=sync_draft)
            opay_diff = opay_start - opay_end
            st.divider()
            st.markdown("### 🖨️ Kyocera")
            k_end = st.number_input("Counter End", step=1, key="k1end", on_change=sync_draft)
            k_os = st.number_input("One-Side", step=1, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("Duplex", step=1, key="k1dp", on_change=sync_draft)
            k_err = st.number_input("Errors / Jam", step=1, key="k1err", on_change=sync_draft)
            k_test = st.number_input("Test / Draft", step=1, key="k1tst", on_change=sync_draft)
            k_actual = k_end - k_start
            k_accounted = k_os + (k_dp * 2) + k_err + k_test
            if (k_accounted - k_actual) == 0: st.success(f"✅ Match (Used: {k_actual})")
            else: st.error(f"⚠️ Diff: {k_accounted - k_actual}")
            st.divider()
            st.markdown("### 🖨️ Xerox")
            x_end = st.number_input("Counter End (X)", step=1, key="x2end", on_change=sync_draft)
            x_os = st.number_input("One-Side (X)", step=1, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("Duplex (X)", step=1, key="x2dp", on_change=sync_draft)
            x_err = st.number_input("Errors (X)", step=1, key="x2err", on_change=sync_draft)
            x_test = st.number_input("Test (X)", step=1, key="x2tst", on_change=sync_draft)
            x_actual = x_end - x_start
            x_accounted = x_os + (x_dp * 2) + x_err + x_test
            if (x_accounted - x_actual) == 0: st.success(f"✅ Match (Used: {x_actual})")
            else: st.error(f"⚠️ Diff: {x_accounted - x_actual}")

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
    wa_msg = f"*🚀 NMS FULL REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n*💰 FINANCIALS:*\n- Sales: {sys_sales:,.2f}\n- Expenses: {expenses:,.2f} ({exp_details_str})\n- Drawer: {t_close:,.2f}\n- *Status:* {diff_status}\n\n*🖨️ PRINTERS:*\n- Kyo Used: {k_actual}\n- Xerox Used: {x_actual}"

    if st.button("🏁 SUBMIT & ARCHIVE FULL SHIFT DATA", use_container_width=True):
        archive_data = {
            "date": datetime.now().strftime('%Y-%m-%d'), "time": datetime.now().strftime('%H:%M:%S'),
            "staff": st.session_state['user'], "branch": branch, "shift": shift,
            "opening_cash": t_open, "sales": sys_sales, "debit_in": u10_debit,
            "expenses": expenses, "exp_details": exp_details_str, "e_pay": t_e_pay,
            "debit_pending": v22_debit, "expected_cash": expected_cash, "actual_cash": t_close,
            "net_diff": net_diff, "opay_move": opay_diff, "kyo_used": k_actual, "xerox_used": x_actual,
            "t_open_count": len([t for t in db['tasks']['opening'] if st.session_state.get(f's_{t}')]),
            "t_close_count": len([t for t in db['tasks']['closing'] if st.session_state.get(f'e_{t}')]),
            "t_social_count": len([t for t in db['tasks']['social'] if st.session_state.get(f'm_{t}')])
        }
        db["history"].append(archive_data); db["pending_debit"] = v22_debit
        db["drafts"][st.session_state['user']] = {}; st.session_state.exp_list = []
        save_db(db); st.success("Shift Archived Successfully!"); st.rerun()

    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD FULL PDF REPORT", use_container_width=True):
            buffer = io.BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=letter); elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"NMS DAILY REPORT - {branch}", styles['Title']))
            data_f = [["Item", "Amount"], ["Sales", sys_sales], ["Expenses", expenses], ["Drawer", t_close], ["Diff", net_diff]]
            t1 = Table(data_f, colWidths=[200, 100]); t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
            elements.append(t1); elements.append(Spacer(1,12))
            elements.append(Paragraph(f"Expense Details: {exp_details_str}", styles['Normal']))
            doc.build(elements)
            st.download_button("💾 Save PDF Report", data=buffer.getvalue(), file_name=f"NMS_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf")

    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND FULL WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
