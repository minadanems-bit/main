import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
import io
import base64
import urllib.parse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. Database Configuration ---
DB_FILE = 'nms_enterprise_pro_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "pending_debit": 0.0,
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "expense_categories": ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Rent", "Other"],
            "users": {
                "admin": {
                    "pass": "admin123", "role": "admin", "full_name": "Manager",
                    "phone": "", "national_id": "", "address": "", "email": "",
                    "social_status": "", "qualification": "", "hiring_date": "2024-01-01",
                    "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": []
                }
            },
            "tasks": {
                "opening": [
                    "Fingerprint / بصمة الحضور", "Power On / تشغيل الأجهزة", "Uniform & Name Tag / الزي الرسمي", 
                    "Music & Ambience / تشغيل الموسيقى", "Paper Loaded / تعبئة الورق", "Cash Counted / عد النقدية", 
                    "Clean Windows & Counters / تنظيف الواجهات", "Check Internet / فحص الإنترنت"
                ],
                "closing": [
                    "Save WhatsApp Contacts / حفظ جهات الاتصال", "Place Cleaned / تنظيف المكان", 
                    "Power Off / إطفاء الأجهزة", "Trash Removed / إخراج المهملات", "Fingerprint / بصمة الانصراف", 
                    "Daily Report Sent / إرسال التقرير", "Safe Locked / إغلاق الخزنة"
                ],
                "social": [
                    "Canva Design 1", "Canva Design 2", "WhatsApp Story", "WhatsApp Channel", 
                    "Facebook Account Story", "Facebook Account Post/Reel", "Facebook Account Group", 
                    "Facebook Page Story", "Facebook Page Post/Reel", "Threads Post", 
                    "Instagram Story", "Instagram Post/Reel", "TikTok Story", "TikTok Post", 
                    "Telegram Story", "Telegram Channel", "LinkedIn Post"
                ],
                "interaction": [
                    "Like / إعجاب", "Love / أحببته", "Care / أدعمه", "Share / مشاركة", 
                    "Comment / تعليق", "Reply to Messages / الرد على الرسائل"
                ]
            },
            "history": [],
            "drafts": {},
            "logs": []
        }
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Ensure new keys exist if updating from older version
        if "tasks" not in data: data["tasks"] = {}
        return data

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

# --- 2. Setup & Session ---
st.set_page_config(page_title="NMS ERP Pro - Stable", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        draft_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_','o_','e_','c_','m_','i_','ks','xs','op','u10','v22','ex','kj','xj','dn'))}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = draft_data
        save_db(db)

# --- 3. Login System ---
if not st.session_state['logged_in']:
    st.title("🔐 NMS Enterprise Management")
    c1, c2 = st.columns(2)
    with c1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=300)
    with c2:
        u = st.selectbox("Employee Name / اسم الموظف", list(db["users"].keys()))
        p = st.text_input("Password / كلمة المرور", type="password")
        if st.button("Login / دخول", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items(): st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Incorrect Password")
else:
    # --- 4. Sidebar: THE MASTER ADMIN CONTROL ---
    with st.sidebar:
        st.header(f"Welcome, {db['users'][st.session_state['user']]['full_name']}")
        if st.button("🚪 Logout / خروج", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Master Admin Suite")
            admin_choice = st.selectbox("Management Area", [
                "HR & Employee Profiles", 
                "Payroll & Development", 
                "Tasks Management", 
                "Branches & Expenses", 
                "Archives & Logs"
            ])

            if admin_choice == "HR & Employee Profiles":
                target = st.selectbox("Select Account", list(db["users"].keys()))
                u_data = db["users"][target]
                with st.expander("Edit Personal Information", expanded=False):
                    u_full = st.text_input("Full Name", value=u_data.get('full_name', ''))
                    u_pass = st.text_input("Password", value=u_data.get('pass', ''))
                    u_phone = st.text_input("Phone", value=u_data.get('phone', ''))
                    u_nid = st.text_input("National ID", value=u_data.get('national_id', ''))
                    u_addr = st.text_area("Address", value=u_data.get('address', ''))
                    u_mail = st.text_input("Email", value=u_data.get('email', ''))
                    u_stat = st.selectbox("Social Status", ["Single", "Married", "Other"], index=0)
                    u_qual = st.text_input("Qualification", value=u_data.get('qualification', ''))
                    if st.button("Save Profile"):
                        db["users"][target].update({
                            "full_name": u_full, "pass": u_pass, "phone": u_phone,
                            "national_id": u_nid, "address": u_addr, "email": u_mail,
                            "social_status": u_stat, "qualification": u_qual
                        })
                        save_db(db); st.success("Updated")
                
                if st.button("➕ Add New Employee"):
                    new_id = st.text_input("New Username (Unique)")
                    if new_id and new_id not in db["users"]:
                        db["users"][new_id] = {"pass": "123", "role": "user", "full_name": new_id, "bonus":[], "deductions":[], "overtime":[], "extra_leaves":[]}
                        save_db(db); st.rerun()

            elif admin_choice == "Payroll & Development":
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                u_fin = db["users"][target]
                new_sal = st.number_input("Base Salary", value=float(u_fin.get('salary', 0)))
                hire_dt = st.date_input("Hiring Date", value=datetime.strptime(u_fin.get('hiring_date', "2024-01-01"), "%Y-%m-%d"))
                if st.button("Update Salary"):
                    db["users"][target]["salary"] = new_sal
                    db["users"][target]["hiring_date"] = str(hire_dt)
                    save_db(db); st.success("Saved")
                st.divider()
                dev_type = st.radio("Add Entry", ["Bonus", "Deduction", "Overtime", "Extra Leave"], horizontal=True)
                d_amt = st.number_input("Amount/Value", step=10.0)
                d_reason = st.text_area("Note")
                if st.button(f"Add {dev_type}"):
                    key = dev_type.lower().replace(" ", "_")
                    if key not in db["users"][target]: db["users"][target][key] = []
                    db["users"][target][key].append({"date": str(date.today()), "val": d_amt, "note": d_reason})
                    save_db(db); st.success("Entry Recorded")

            elif admin_choice == "Tasks Management":
                t_cat = st.selectbox("Category", ["opening", "closing", "social", "interaction"])
                for i, t in enumerate(db["tasks"][t_cat]):
                    c_t1, c_t2 = st.columns([4, 1])
                    c_t1.text(f"• {t}")
                    if c_t2.button("🗑️", key=f"dt_{t_cat}_{i}"):
                        db["tasks"][t_cat].pop(i); save_db(db); st.rerun()
                nt = st.text_input("New Task Description")
                if st.button("Add Task"):
                    if nt: db["tasks"][t_cat].append(nt); save_db(db); st.rerun()

            elif admin_choice == "Branches & Expenses":
                st.write("### Branches")
                for i, b in enumerate(db["branches"]):
                    cb1, cb2 = st.columns([4,1]); cb1.text(b)
                    if cb2.button("🗑️", key=f"br_{i}"): db["branches"].pop(i); save_db(db); st.rerun()
                nb = st.text_input("New Branch")
                if st.button("Add Branch"): db["branches"].append(nb); save_db(db); st.rerun()
                st.divider()
                st.write("### Expenses")
                for i, e in enumerate(db["expense_categories"]):
                    ce1, ce2 = st.columns([4,1]); ce1.text(e)
                    if ce2.button("🗑️", key=f"ex_{i}"): db["expense_categories"].pop(i); save_db(db); st.rerun()
                ne = st.text_input("New Expense Cat")
                if st.button("Add Expense Category"): db["expense_categories"].append(ne); save_db(db); st.rerun()

    # --- 5. Main Content: DAILY OPERATIONS ---
    st.title("📊 NMS Enterprise - Daily Operations")
    m1, m2, m3, m4 = st.columns(4)
    with m1: branch = st.selectbox("Branch Location", db["branches"])
    with m2: shift = st.selectbox("Shift Type", ["Morning", "Night"])
    with m3: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    with m4: st.info(f"👤 User: {st.session_state['user']}")

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING", "🔴 TAB 2: CLOSING", "📱 TAB 3: SOCIAL"])

    # --- TAB 1: OPENING ---
    with tab1:
        st.subheader("Opening Checklist & Initial State")
        col_o1, col_o2, col_o3 = st.columns([1, 1.5, 1.5])
        with col_o1:
            st.markdown("#### ✅ Tasks")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with col_o2:
            st.markdown("#### 💵 Cash (Drawer)")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Opening Coins", step=0.5, key="o_coins", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total: {t_open:,.2f}**")
        with col_o3:
            st.markdown("#### 🔢 Start Counters")
            ks = st.number_input("Kyocera Start", step=1, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Start", step=0.01, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit U10 (In)", step=1.0, key="u10_val", on_change=sync_draft)

    # --- TAB 2: CLOSING ---
    with tab2:
        st.subheader("Shift End & Financial Detail")
        col_c1, col_c2, col_c3 = st.columns([1, 1.5, 1.5])
        with col_c1:
            st.markdown("#### ✅ Tasks")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.markdown("#### 💻 System & Electronic")
            sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales", on_change=sync_draft)
            instapay = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1.0, key="c_visa", on_change=sync_draft)
            v22 = st.number_input("Debit V22 (Out)", step=1.0, key="v22_val", on_change=sync_draft)
        with col_c2:
            st.markdown("#### 💵 Actual Cash (Drawer)")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, key="c_coins", on_change=sync_draft)
            t_close += c_coins
            st.divider()
            st.markdown("#### 💸 Expenses")
            ex_cat = st.selectbox("Category", db["expense_categories"], key="ex_cat")
            ex_val = st.number_input("Expense Amount", step=1.0, key="ex_val")
            ex_note = st.text_input("Expense Reason", key="ex_note")
            
            # MATH
            expected = t_open + sys_sales + u10 - ex_val - v22 - (instapay + wallet + visa)
            diff = t_close - expected
            st.metric("Expected Drawer", f"{expected:,.2f}")
            if abs(diff) < 0.1: st.success("Matched!")
            else: st.error(f"Diff: {diff:,.2f}")

        with col_c3:
            st.markdown("#### 🖨️ Detailed Printers & Opay")
            st.write("**Kyocera**")
            ke = st.number_input("Kyo End", step=1, key="ke")
            k1s = st.number_input("Kyo 1-Side", step=1, key="k1s")
            k2s = st.number_input("Kyo 2-Sides", step=1, key="k2s")
            kj = st.number_input("Kyo Paper Jam / حشر ورق", step=1, key="kj", on_change=sync_draft)
            
            st.write("**Xerox**")
            xe = st.number_input("Xerox End", step=1, key="xe")
            x1s = st.number_input("Xerox 1-Side", step=1, key="x1s")
            x2s = st.number_input("Xerox 2-Sides", step=1, key="x2s")
            xj = st.number_input("Xerox Paper Jam / حشر ورق", step=1, key="xj", on_change=sync_draft)
            
            st.divider()
            ope = st.number_input("Opay Final", step=0.01, key="ope")
            st.info(f"Opay Movement: {ops - ope:,.2f}")
            
            st.divider()
            st.write("**Draft Notes / مسودة الملاحظات**")
            st.text_area("Write any internal notes here...", key="dn_notes", on_change=sync_draft)

    # --- TAB 3: SOCIAL ---
    with tab3:
        st.subheader("Social Media, Interaction & PDF")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("#### 📱 Marketing Tasks")
            for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        with sc2:
            st.markdown("#### 🤝 Interaction Tasks")
            for t in db["tasks"]["interaction"]: st.checkbox(t, key=f"i_{t}", on_change=sync_draft)

        st.divider()
        # Full Report for WA
        wa_text = f"*🚀 NMS FINAL REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n" \
                  f"*💰 Finance:*\n- Sales: {sys_sales:,.2f}\n- Exp: {ex_val:,.2f}\n- Drawer: {t_close:,.2f}\n- Diff: {diff:,.2f}\n\n" \
                  f"*🖨️ Printers (Kyo | Xerox):*\n- Kyo Total: {ke-ks} (Jam: {kj})\n- Xerox Total: {xe-xs} (Jam: {xj})\n\n" \
                  f"*💳 Systems:*\n- Opay Move: {ops-ope:,.2f}\n- V22: {v22:,.2f}"

        if st.button("🏁 FINISH & ARCHIVE DAY", use_container_width=True):
            entry = {"date": str(date.today()), "branch": branch, "sales": sys_sales, "diff": diff}
            db["history"].append(entry)
            save_db(db); st.success("Shift Archived")

        crep1, crep2 = st.columns(2)
        with crep1:
            if st.button("📄 GENERATE FULL PDF", use_container_width=True):
                buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
                styles = getSampleStyleSheet(); parts = [Paragraph(f"NMS Full Report - {branch} - {date.today()}", styles['Title'])]
                p_data = [["Category", "Detail"], ["Sales", sys_sales], ["Expenses", ex_val], ["Kyo Jam", kj], ["Xerox Jam", xj]]
                tbl = Table(p_data, colWidths=[200, 300])
                tbl.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
                parts.append(tbl); doc.build(parts)
                st.download_button("📥 Save PDF", buf.getvalue(), f"NMS_Report_{date.today()}.pdf")
        with crep2:
            url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
