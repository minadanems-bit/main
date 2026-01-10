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
            "pending_orders": 0.0,  # خانة المبيت العامة
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager", "email": "admin@nms.com", "phone": "000", "id_num": "000", "address": "HQ", "photo": None},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None}
            },
            "branches": ["Mohamed Nagib Branch", "El Tram Branch"],
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
        # الحفظ التلقائي لكل المدخلات التي تبدأ ببادئات النظام
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_'))}
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
        # عرض المبيت المُرحل من الشفت السابق
        if db.get("pending_orders", 0) > 0:
            st.warning(f"📦 تنبيه: يوجد أوردرات مبيتة من الشفت السابق بقيمة: {db['pending_orders']:,.2f} جنيه (سيتم استلام كاش خاص بها)")
        
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Opening Checklist**")
            for t in db["tasks"]["opening"]: 
                st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
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
            st.write("**Start Counters**")
            k_start = st.number_input("Kyocera Opening", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Opening", step=1, key="xs", on_change=sync_draft)
            opay_start = st.number_input("Opay Opening Balance", step=0.01, format="%.4f", key="ops", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: 
                st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.write("**Financial Input**")
            sys_sales = st.number_input("System Sales (SQL)", min_value=0.0, step=1.0, key="c_sys_sales", on_change=sync_draft)
            # إضافة خانة المبيت الجديدة
            mabeet = st.number_input("مبيت (أوردرات طُبعت ولم تستلم)", min_value=0.0, step=1.0, key="c_mabeet", on_change=sync_draft)
            
            instapay = st.number_input("Instapay", step=1, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1, key="c_visa", on_change=sync_draft)
        with c2:
            st.write("**Closing Cash (Physical)**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE  ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins  ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            expenses = st.number_input("Expenses", step=1, key="c_exp", on_change=sync_draft)
            
            st.divider()
            # المعادلة المعدلة: المبيت يُطرح من المتوقع لأنه لم يدخل الدرج كاش
            expected_cash = t_open + sys_sales - expenses - mabeet
            net_diff = t_close - expected_cash
            
            st.metric("Expected Cash", f"{expected_cash:,.2f} LE")
            if net_diff == 0: st.success("✅ Match")
            elif net_diff > 0: st.warning(f"➕ Surplus: {net_diff:,.2f}")
            else: st.error(f"➖ Shortage: {net_diff:,.2f}")

        with c3:
            st.write("**Printer Analysis**")
            k_end = st.number_input("Kyo Final", step=1, key="k1end", on_change=sync_draft)
            k_os = st.number_input("Kyo One-Side", step=1, key="k1os", on_change=sync_draft)
            k_dp = st.number_input("Kyo Duplex", step=1, key="k1dp", on_change=sync_draft)
            k_actual = k_end - k_start
            k_manual = k_os + (k_dp * 2)
            st.warning(f"Kyo Diff: {k_manual - k_actual}")
            
            x_end = st.number_input("Xerox Final", step=1, key="x2end", on_change=sync_draft)
            x_os = st.number_input("Xerox One-Side", step=1, key="x2os", on_change=sync_draft)
            x_dp = st.number_input("Xerox Duplex", step=1, key="x2dp", on_change=sync_draft)
            x_actual = x_end - x_start
            x_manual = x_os + (x_dp * 2)
            st.warning(f"Xerox Diff: {x_manual - x_actual}")
            opay_end = st.number_input("Opay Final", step=0.01, format="%.4f", key="op_end", on_change=sync_draft)

    with tab3:
        st.subheader("Social Media Tasks")
        m_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["social"]):
            m_cols[i%4].checkbox(task, key=f"m_{task}", on_change=sync_draft)
        st.divider(); st.write("**Interaction**")
        i_cols = st.columns(4)
        for i, task in enumerate(db["tasks"]["interaction"]):
            i_cols[i%4].checkbox(task, key=f"i_{task}", on_change=sync_draft)

    # --- 6. Exporting (WhatsApp & PDF) ---
    st.divider()
    opening_tasks_done = [t for t in db["tasks"]["opening"] if st.session_state.get(f"s_{t}")]
    closing_tasks_done = [t for t in db["tasks"]["closing"] if st.session_state.get(f"e_{t}")]
    social_tasks_done = [t for t in db["tasks"]["social"] if st.session_state.get(f"m_{t}")]
    
    diff_status = "✅ Match" if net_diff == 0 else f"➕ Surplus: {net_diff}" if net_diff > 0 else f"➖ Shortage: {net_diff}"
    wa_msg = f"*🚀 NMS FULL REPORT*\n*Date:* {datetime.now().strftime('%Y-%m-%d')}\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n*💰 FINANCIAL:*\n- System Sales: {sys_sales:,.2f}\n- Mabeet (Pending): {mabeet:,.2f}\n- Expenses: {expenses:,.2f}\n- Actual Cash: {t_close:,.2f}\n- *Status:* {diff_status}\n\n*🖨️ PRINTERS:*\n- Kyo Actual: {k_actual}\n- Xerox Actual: {x_actual}\n\n*✅ TASKS DONE:* {len(opening_tasks_done)+len(closing_tasks_done)+len(social_tasks_done)}"

    rep1, rep2 = st.columns(2)
    with rep1:
        if st.button("📥 DOWNLOAD FULL PDF REPORT", use_container_width=True):
            # ترحيل قيمة المبيت لقاعدة البيانات عند استخراج التقرير النهائي
            db["pending_orders"] = mabeet
            save_db(db)
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = [Paragraph(f"NMS DAILY REPORT - {branch}", styles['Title']), Spacer(1, 12)]
            
            # Table 1: Financials with Mabeet
            data_fin = [
                ["Category", "Amount (LE)"],
                ["Opening Cash", f"{t_open:,.2f}"],
                ["System Sales", f"{sys_sales:,.2f}"],
                ["Mabeet (Pending)", f"{mabeet:,.2f}"],
                ["Expenses", f"{expenses:,.2f}"],
                ["Expected Cash", f"{expected_cash:,.2f}"],
                ["Actual Cash", f"{t_close:,.2f}"],
                ["Difference", f"{net_diff:,.2f}"]
            ]
            t_f = Table(data_fin, colWidths=[200, 100])
            t_f.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (1,0), colors.grey), ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke)]))
            elements.append(Paragraph("Financial Summary", styles['Heading2']))
            elements.append(t_f)
            
            # Table 2: Printers
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("Printer Analysis", styles['Heading2']))
            data_p = [
                ["Printer", "Start", "End", "Actual", "Manual"],
                ["Kyocera", k_start, k_end, k_actual, k_manual],
                ["Xerox", x_start, x_end, x_actual, x_manual]
            ]
            t_p = Table(data_p, colWidths=[100, 60, 60, 60, 60])
            t_p.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
            elements.append(t_p)

            doc.build(elements)
            st.download_button("Click to Save PDF", data=buffer.getvalue(), file_name=f"NMS_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf")

    with rep2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND FULL WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
