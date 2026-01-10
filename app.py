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

# دالة الحفظ التلقائي للمسودة
def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # حفظ كل المدخلات التي تبدأ بـ مفاتيح معينة
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2'))}
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
                # استعادة المسودة فور تسجيل الدخول
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items():
                        st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Authentication Failed")

else:
    # --- 4. Sidebar (Admin & Profile) ---
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

        # --- ADMIN MASTER CONTROLS ---
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

                col_actions = st.columns(2)
                with col_actions[0]:
                    if st.button("💾 Save Changes"): save_db(db); st.success("Updated!")
                with col_actions[1]:
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
                cat = st.selectbox("Category", ["Opening Checklist (Tab 1)", "Closing Checklist (Tab 2)", "Social Media Tasks (Tab 3)"])
                t_key = "opening" if "1" in cat else "closing" if "2" in cat else "social"
                
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
            k_start = st.number_input("Kyocera Opening Counter", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Opening Counter", step=1, key="xs", on_change=sync_draft)
            opay_start = st.number_input("Opay Opening Balance", step=0.01, format="%.4f", key="ops", on_change=sync_draft)

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: 
                st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider(); st.write("**Non-Cash**")
            instapay = st.number_input("Instapay", step=1, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1, key="c_visa", on_change=sync_draft)
        with c2:
            st.write("**Closing Cash**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, format="%.2f", key="cc", on_change=sync_draft)
            t_close += c_coins
            expenses = st.number_input("Expenses", step=1, key="c_exp", on_change=sync_draft)
            net_diff = (t_close + expenses) - t_open
            st.metric("Net Cash Difference", f"{net_diff:,.2f} LE")
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

    # --- 6. Exporting ---
    st.divider()
    wa_msg = f"*🚀 NMS REPORT*\nBranch: {branch}\nCash Diff: {net_diff:,.2f}"
    if st.button("📥 EXPORT PDF REPORT"):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = [Paragraph(f"NMS REPORT - {branch}", getSampleStyleSheet()['Title'])]
        doc.build(elements)
        st.download_button("Download", data=buffer.getvalue(), file_name=f"{branch}.pdf")
    
    wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank">📱 SEND TO WHATSAPP</a>', unsafe_allow_html=True)
