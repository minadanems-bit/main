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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
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
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina", "photo": None},
                "Youstina": {"pass": "123", "role": "user", "full_name": "Youstina", "photo": None},
                "Mark": {"pass": "123", "role": "user", "full_name": "Mark", "photo": None},
                "Fatma": {"pass": "123", "role": "user", "full_name": "Fatma", "photo": None}
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

# --- 2. Styling & Session ---
st.set_page_config(page_title="NMS Management System", layout="wide")
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

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
                
                # 1. إضافة موظف جديد تماماً
                with st.expander("➕ Register New Employee"):
                    new_u_name = st.text_input("Username (Login ID)")
                    new_u_pass = st.text_input("Set Password", type="password")
                    new_u_full = st.text_input("Full Name")
                    if st.button("Create Account"):
                        if new_u_name and new_u_name not in db["users"]:
                            db["users"][new_u_name] = {
                                "pass": new_u_pass, 
                                "role": "user", 
                                "full_name": new_u_full,
                                "email": "", "phone": "", "address": "", "id_num": "", "photo": None
                            }
                            save_db(db)
                            st.success(f"Account for {new_u_name} created successfully!")
                            st.rerun()
                        else: st.error("Username empty or already exists!")

                st.divider()

                # 2. تعديل أو مسح موظف موجود
                st.write("**Manage Existing Accounts**")
                target_user = st.selectbox("Select Employee", list(db["users"].keys()))
                
                # نمنع المدير من مسح نفسه بالخطأ
                is_admin = db["users"][target_user]["role"] == "admin"
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    db["users"][target_user]["full_name"] = st.text_input("Full Name", db["users"][target_user].get("full_name", ""))
                    db["users"][target_user]["pass"] = st.text_input("Edit Password", db["users"][target_user]["pass"])
                    db["users"][target_user]["phone"] = st.text_input("Phone", db["users"][target_user].get("phone", ""))
                
                with col_e2:
                    db["users"][target_user]["address"] = st.text_input("Address", db["users"][target_user].get("address", ""))
                    db["users"][target_user]["email"] = st.text_input("Email", db["users"][target_user].get("email", ""))
                    db["users"][target_user]["id_num"] = st.text_input("ID Number", db["users"][target_user].get("id_num", ""))

                col_actions = st.columns(2)
                with col_actions[0]:
                    if st.button("💾 Save Changes", use_container_width=True):
                        save_db(db)
                        st.success(f"Details for {target_user} updated!")
                
                with col_actions[1]:
                    if not is_admin: # حماية حساب الأدمن من المسح
                        if st.button("🗑️ Delete Employee", use_container_width=True):
                            del db["users"][target_user]
                            save_db(db)
                            st.warning(f"User {target_user} deleted!")
                            st.rerun()
                    else:
                        st.info("Admin account cannot be deleted.")

            elif admin_mode == "Manage Branches":
                st.subheader("🏢 Branch Management")
                
                # 1. إضافة فرع جديد
                with st.expander("➕ Add New Branch"):
                    n_br = st.text_input("New Branch Name")
                    if st.button("Confirm Add"):
                        if n_br and n_br not in db["branches"]:
                            db["branches"].append(n_br)
                            save_db(db)
                            st.success(f"Branch '{n_br}' added!")
                            st.rerun()
                        else: st.error("Branch name empty or already exists")

                st.divider()

                # 2. تعديل أو حذف فرع موجود
                st.write("**Edit or Remove Existing Branch**")
                target_br = st.selectbox("Select Branch to Modify", db["branches"])
                
                col_br1, col_br2 = st.columns(2)
                
                with col_br1:
                    new_br_name = st.text_input("New Name for Branch", value=target_br)
                    if st.button("📝 Update Branch Name"):
                        if new_br_name:
                            index = db["branches"].index(target_br)
                            db["branches"][index] = new_br_name
                            save_db(db)
                            st.success(f"Changed from {target_br} to {new_br_name}")
                            st.rerun()

                with col_br2:
                    st.write("⚠️ **Danger Zone**")
                    if st.button("🗑️ Delete This Branch"):
                        if len(db["branches"]) > 1: # نترك فرع واحد على الأقل للنظام
                            db["branches"].remove(target_br)
                            save_db(db)
                            st.warning(f"Branch '{target_br}' has been deleted.")
                            st.rerun()
                        else:
                            st.error("Cannot delete the only remaining branch!")

            elif admin_mode == "Manage Tasks":
                st.subheader("📝 Universal Task Management")
                
                # قائمة منسدلة لاختيار القائمة التي تريد تعديلها
                category = st.selectbox("Select Category to Edit", 
                                        ["Opening Checklist (Tab 1)", 
                                         "Closing Checklist (Tab 2)", 
                                         "Social Media Tasks (Tab 3)"])
                
                # تحديد المفتاح البرمجي بناءً على الاختيار
                if category == "Opening Checklist (Tab 1)":
                    task_key = "opening"
                elif category == "Closing Checklist (Tab 2)":
                    task_key = "closing"
                else:
                    task_key = "social"

                st.divider()
                st.write(f"### Manage {category}")

                # 1. إضافة بند جديد
                col_add, col_btn = st.columns([3, 1])
                with col_add:
                    new_item = st.text_input(f"New Item for {category}", placeholder="Type task name here...")
                with col_btn:
                    st.write(" ") # موازنة رأسية
                    if st.button("➕ Add Item", use_container_width=True):
                        if new_item and new_item not in db["tasks"][task_key]:
                            db["tasks"][task_key].append(new_item)
                            save_db(db)
                            st.success("Task Added!")
                            st.rerun()
                        else: st.error("Empty or Duplicate!")

                st.divider()

                # 2. حذف بند موجود
                st.write("**Current Tasks (Select to Remove):**")
                item_to_del = st.selectbox("Select Task", db["tasks"][task_key], key="del_selector")
                
                if st.button("🗑️ Delete Selected Item", use_container_width=True):
                    if item_to_del:
                        db["tasks"][task_key].remove(item_to_del)
                        save_db(db)
                        st.warning(f"Item '{item_to_del}' removed.")
                        st.rerun()

            elif admin_mode == "Audit Logs":
                st.subheader("📜 System Logs")
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
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}")
        with c2:
            st.write("**Opening Cash**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}")
                t_open += (v * d)
            o_coins = st.number_input("Coins (Decimal)", step=0.5, format="%.2f", key="oc")
            t_open += o_coins
            st.success(f"**Total Opening: {t_open:,.2f} LE**")
        with c3:
            st.write("**Start Counters**")
            k_start = st.number_input("Kyocera Opening Counter", step=1, key="ks")
            x_start = st.number_input("Xerox Opening Counter", step=1, key="xs")
            opay_start = st.number_input("Opay Opening Balance", step=0.01, format="%.4f", key="ops")

    with tab2:
        st.subheader("Closing Procedures")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}")
            st.divider(); st.write("**Non-Cash**")
            instapay = st.number_input("Instapay", step=1); wallet = st.number_input("Wallet", step=1); visa = st.number_input("Visa", step=1)
        with c2:
            st.write("**Closing Cash**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}")
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, format="%.2f", key="cc")
            t_close += c_coins
            expenses = st.number_input("Expenses", step=1)
            net_diff = (t_close + expenses) - t_open
            st.metric("Net Cash Difference", f"{net_diff:,.2f} LE")
        with c3:
            st.write("**Printer Usage Analysis**")
            # Kyocera
            st.markdown("--- *Kyocera (P1)* ---")
            k_end = st.number_input("Kyo Final Counter", step=1)
            k_os = st.number_input("Kyo One-Side", step=1, key="k1os")
            k_dp = st.number_input("Kyo Duplex (Sheets)", step=1, key="k1dp")
            k_dr = st.number_input("Kyo Draft/Error", step=1, key="k1dr")
            k_actual = k_end - k_start
            k_manual = k_os + (k_dp * 2) + k_dr
            st.warning(f"Kyo Diff: {k_manual - k_actual}")
            # Xerox
            st.markdown("--- *Xerox (P2)* ---")
            x_end = st.number_input("Xerox Final Counter", step=1)
            x_os = st.number_input("Xerox One-Side", step=1, key="x2os")
            x_dp = st.number_input("Xerox Duplex (Sheets)", step=1, key="x2dp")
            x_dr = st.number_input("Xerox Draft/Error", step=1, key="x2dr")
            x_actual = x_end - x_start
            x_manual = x_os + (x_dp * 2) + x_dr
            st.warning(f"Xerox Diff: {x_manual - x_actual}")
            # Opay
            st.divider(); opay_end = st.number_input("Opay Final Balance", step=0.01, format="%.4f")

    with tab3:
        st.subheader("Social Media Tasks")
        m_cols = st.columns(4)
        m_res = {task: m_cols[i%4].checkbox(task, key=f"m_{task}") for i, task in enumerate(db["tasks"]["social"])}
        st.divider(); st.write("**Interaction Tasks**")
        i_cols = st.columns(4)
        i_res = {task: i_cols[i%4].checkbox(task, key=f"i_{task}") for i, task in enumerate(db["tasks"]["interaction"])}

    # --- 6. Report Generation ---
    st.divider()
    b1, b2 = st.columns(2)
    
    wa_msg = f"*🚀 NMS DAILY REPORT*\n" \
             f"Branch: {branch} | Staff: {st.session_state['user']}\n" \
             f"Cash Diff: {net_diff:,.2f} LE\n" \
             f"P1 Usage: {k_manual} | P2 Usage: {x_manual}\n" \
             f"Opay Diff: {opay_end - opay_start:,.4f}"

    with b1:
        if st.button("📥 EXPORT PDF REPORT", use_container_width=True):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"NMS SYSTEM REPORT - {branch}", styles['Title']))
            elements.append(Paragraph(f"Employee: {st.session_state['user']} | Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            tbl_data = [["Metric", "Value"], ["Net Cash Diff", f"{net_diff}"], ["Kyocera Total", f"{k_manual}"], ["Xerox Total", f"{x_manual}"], ["Opay Diff", f"{opay_end-opay_start}"]]
            t = Table(tbl_data, colWidths=[200, 200])
            t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
            elements.append(t); doc.build(elements)
            st.download_button("Download Now", data=buffer.getvalue(), file_name=f"Report_{branch}.pdf")

    with b2:
        wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND TO WHATSAPP</button></a>', unsafe_allow_html=True)

    # Save Drafts Automaticaly
    save_db(db)
