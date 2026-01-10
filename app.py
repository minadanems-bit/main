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
            "branches": ["M. Nagib Branch", "Tram Branch"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform & Name Tag", "Music On", "Paper Loaded", "Cash Counted", "All Good"],
                "closing": ["Contacts on WhatsApp", "Place Cleaned", "Power Off", "Cash Counted", "Fingerprint", "Report Sent"],
                "social": ["Canva 1", "Canva 2", "WhatsApp Story", "WhatsApp Channel", "Facebook account Story", "Facebook account Post / Reel", "Facebook account Group", "Facebook Page Story", "Facebook Page Post / Reel", "Threads", "Instagram Story", "Instagram Post / Reel", "TikTok Story", "TikTok Post", "Telegram Story", "Telegram Channel", "LinkedIn Post"],
                "interaction": ["Like", "Love", "Care", "Share"]
            },
            "logs": [],
            "drafts": {}
        }
    with open(DB_FILE, 'r') as f: return json.load(f)

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
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_'))}
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
            admin_mode = st.radio("Settings", ["Manage Employees", "Manage Branches", "Manage Tasks", "Audit Logs"])
            
            if admin_mode == "Manage Employees":
                st.subheader("👥 Employee Master Control")
                with st.expander("➕ Register New Employee"):
                    new_u_name = st.text_input("Username (Login ID)")
                    new_u_pass = st.text_input("Set Password", type="password")
                    new_u_full = st.text_input("Full Name")
                    if st.button("Create Account"):
                        if new_u_name and new_u_name not in db["users"]:
                            db["users"][new_u_name] = {"pass": new_u_pass, "role": "user", "full_name": new_u_full}
                            save_db(db); st.success(f"Account for {new_u_name} created!"); st.rerun()
                st.divider()
                target_user = st.selectbox("Select Employee", list(db["users"].keys()))
                is_admin = db["users"][target_user]["role"] == "admin"
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    db["users"][target_user]["full_name"] = st.text_input("Full Name", db["users"][target_user].get("full_name", ""))
                    db["users"][target_user]["pass"] = st.text_input("Password", db["users"][target_user]["pass"])
                with col_e2:
                    db["users"][target_user]["phone"] = st.text_input("Phone", db["users"][target_user].get("phone", ""))
                    db["users"][target_user]["address"] = st.text_input("Address", db["users"][target_user].get("address", ""))
                if st.button("💾 Save Changes"): save_db(db); st.success("Updated!")
                if not is_admin and st.button("🗑️ Delete Employee"):
                    del db["users"][target_user]; save_db(db); st.warning("Deleted!"); st.rerun()

            elif admin_mode == "Manage Branches":
                st.subheader("🏢 Branch Management")
                n_br = st.text_input("New Branch Name")
                if st.button("Add Branch"):
                    db["branches"].append(n_br); save_db(db); st.rerun()
                target_br = st.selectbox("Edit/Delete Branch", db["branches"])
                new_br_name = st.text_input("Rename to", value=target_br)
                if st.button("📝 Update Name"):
                    idx = db["branches"].index(target_br); db["branches"][idx] = new_br_name
                    save_db(db); st.rerun()
                if st.button("🗑️ Delete Branch") and len(db["branches"]) > 1:
                    db["branches"].remove(target_br); save_db(db); st.rerun()

            elif admin_mode == "Manage Tasks":
                st.subheader("📝 Task Management")
                cat = st.selectbox("Category", ["Opening", "Closing", "Social"])
                t_key = cat.lower()
                new_t = st.text_input("Add Task")
                if st.button("➕ Add"): db["tasks"][t_key].append(new_t); save_db(db); st.rerun()
                del_t = st.selectbox("Delete Task", db["tasks"][t_key])
                if st.button("🗑️ Remove"): db["tasks"][t_key].remove(del_t); save_db(db); st.rerun()

            elif admin_mode == "Audit Logs":
                st.dataframe(pd.DataFrame(db["logs"]).tail(50))

    # --- 5. Main Dashboard ---
    st.title("📊 Daily Shift Control")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf1: st.info(f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    with inf2: st.info(f"🕒 **Day:** {datetime.now().strftime('%A')}")
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift = st.selectbox("Shift", ["Morning", "Between", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING", "🔴 TAB 2: CLOSING", "📱 TAB 3: SOCIAL MEDIA"])

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
            u10_debit = st.number_input("Debit Received (Cash In)", min_value=0.0, step=1.0, key="u10_val", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.write("**Financial Input**")
            sys_sales = st.number_input("System Sales", min_value=0.0, step=1.0, key="c_sys_sales", on_change=sync_draft)
            v22_debit = st.number_input("Debit Pending (Unpaid)", min_value=0.0, step=1.0, key="v22_val", on_change=sync_draft)
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
            expenses = st.number_input("Expenses", step=1.0, key="c_exp", on_change=sync_draft)
            
            st.divider()
            # المعادلة المالية (تم استبعاد اوباي منها تماما بناء على طلبك)
            expected_cash = t_open + sys_sales + u10_debit - expenses - v22_debit - t_e_pay
            net_diff = t_close - expected_cash
            st.metric("Expected Cash (Drawer)", f"{expected_cash:,.2f} LE")
            if abs(net_diff) < 0.1: st.success("✅ Match")
            elif net_diff > 0: st.warning(f"➕ Surplus: {net_diff:,.2f}")
            else: st.error(f"➖ Shortage: {net_diff:,.2f}")

        with c3:
            st.write("**Systems Analysis**")
            opay_end = st.number_input("Opay Final Balance", step=0.01, format="%.4f", key="op_end", on_change=sync_draft)
            opay_diff = opay_start - opay_end
            st.write(f"Opay Movement: {opay_diff:,.2f}")
            st.divider()
            st.markdown("### 🖨️ Kyocera")
            k_end = st.number_input("Counter End", step=1, key="k1end", on_change=sync_draft)
            k_os = st.number_input("Sold: One-Side", step=1, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("Sold: Duplex", step=1, key="k1dp", on_change=sync_draft)
            k_err = st.number_input("Errors / Jam", step=1, key="k1err", on_change=sync_draft)
            k_test = st.number_input("Test / Draft", step=1, key="k1tst", on_change=sync_draft)
            k_actual = k_end - k_start
            k_accounted = k_os + (k_dp * 2) + k_err + k_test
            if (k_accounted - k_actual) == 0: st.success(f"✅ Match (Used: {k_actual})")
            else: st.error(f"⚠️ Diff: {k_accounted - k_actual}")
            st.divider()
            st.markdown("### 🖨️ Xerox")
            x_end = st.number_input("Counter End (X)", step=1, key="x2end", on_change=sync_draft)
            x_os = st.number_input("Sold: S (X)", step=1, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("Sold: D (X)", step=1, key="x2dp", on_change=sync_draft)
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
    diff_status = "✅ Match" if abs(net_diff) < 0.1 else f"⚠️ {net_diff}"
    wa_msg = f"*🚀 NMS FULL REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n*💰 FINANCIALS:*\n- Opening Cash: {t_open:,.2f}\n- Total Sales: {sys_sales:,.2f}\n- Debit Received: {u10_debit:,.2f}\n- Expenses: {expenses:,.2f}\n- E-Payments: {t_e_pay:,.2f}\n- Debit Pending: {v22_debit:,.2f}\n- Cash in Drawer: {t_close:,.2f}\n- *Final Status:* {diff_status}\n\n*📱 SYSTEMS:*\n- Opay Movement: {opay_diff:,.2f}\n- Opay Final: {opay_end:,.4f}\n\n*🖨️ PRINTERS:*\n- Kyo Used: {k_actual}\n- Xerox Used: {x_actual}"

    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD FULL PDF REPORT", use_container_width=True):
            db["pending_debit"] = v22_debit; save_db(db)
            buffer = io.BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet(); elements = []
            elements.append(Paragraph(f"NMS DAILY REPORT - {branch}", styles['Title']))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')} | Staff: {st.session_state['user']}", styles['Normal']))
            
            # Financials Table
            data_f = [["Financial Item", "Amount"], ["Opening Cash", t_open], ["Total Sales", sys_sales], ["Debit Received", u10_debit], ["Expenses", expenses], ["E-Payments", t_e_pay], ["Debit Pending", v22_debit], ["Expected Cash", expected_cash], ["Actual Cash", t_close], ["Net Difference", net_diff]]
            t1 = Table(data_f, colWidths=[200, 100])
            t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.indianred), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke)]))
            elements.append(Spacer(1, 15)); elements.append(Paragraph("1. Financial Summary", styles['Heading3'])); elements.append(t1)

            # Systems & Printers Table
            data_p = [["System/Printer", "Start", "End/Used", "Match Status"], ["Opay Wallet", opay_start, opay_end, f"Diff: {opay_diff}"], ["Kyocera", k_start, k_actual, "OK" if (k_accounted-k_actual)==0 else "Err"], ["Xerox", x_start, x_actual, "OK" if (x_accounted-x_actual)==0 else "Err"]]
            t2 = Table(data_p, colWidths=[120, 80, 80, 80])
            t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightblue)]))
            elements.append(Spacer(1, 15)); elements.append(Paragraph("2. Systems & Printers Analysis", styles['Heading3'])); elements.append(t2)

            # Tasks Table
            data_t = [["Task Category", "Done", "Total Available"]]
            data_t.append(["Opening", len([t for t in db['tasks']['opening'] if st.session_state.get(f's_{t}')]), len(db['tasks']['opening'])])
            data_t.append(["Closing", len([t for t in db['tasks']['closing'] if st.session_state.get(f'e_{t}')]), len(db['tasks']['closing'])])
            data_t.append(["Social", len([t for t in db['tasks']['social'] if st.session_state.get(f'm_{t}')]), len(db['tasks']['social'])])
            t3 = Table(data_t, colWidths=[120, 80, 100]); t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.grey)]))
            elements.append(Spacer(1, 15)); elements.append(Paragraph("3. Tasks Execution Summary", styles['Heading3'])); elements.append(t3)

            doc.build(elements)
            st.download_button("💾 Save PDF Report", data=buffer.getvalue(), file_name=f"NMS_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf")

    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND FULL WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
