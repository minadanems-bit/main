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

# --- 1. Database Configuration & Robust Initialization ---
DB_FILE = 'nms_enterprise_pro_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    # الهيكل الكامل والافتراضي لضمان عدم نقص أي خانة مستقبلاً
    default_structure = {
        "logo": None,
        "branches": ["M. Nageb Branch", "Tram Branch"],
        "expense_categories": ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Rent", "Other"],
        "users": {
            "admin": {
                "pass": "admin123", "role": "admin", "full_name": "Manager",
                "phone": "", "national_id": "", "address": "", "email": "",
                "social_status": "Single", "qualification": "", "hiring_date": "2024-01-01",
                "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": []
            }
        },
        "tasks": {
            "opening": [
                "Fingerprint / بصمة الحضور", "Power On / تشغيل الأجهزة", "Uniform & Name Tag / الزي الرسمي", 
                "Music & Ambience / تشغيل الموسيقى", "Paper Loaded / تعبئة الورق", "Cash Counted / عد النقدية", 
                "Clean Windows & Counters / تنظيف الواجهات", "Check Internet / فحص الإنترنت", "Check Supplies / فحص المخزون"
            ],
            "closing": [
                "Save WhatsApp Contacts / حفظ جهات الاتصال", "Place Cleaned / تنظيف المكان", 
                "Power Off / إطفاء الأجهزة", "Trash Removed / إخراج المهملات", "Fingerprint / بصمة الانصراف", 
                "Daily Report Sent / إرسال التقرير", "Safe Locked / إغلاق الخزنة", "Lights Off / إطفاء الأنوار"
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
                "Comment / تعليق", "Reply to Messages / الرد على الرسائل", "Join Groups / دخول جروبات"
            ]
        },
        "history": [], "drafts": {}, "logs": []
    }
    
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return default_structure
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # مراجعة كل الموظفين لضمان وجود الهيكل المالي (HR) كاملاً لكل واحد
        for user in data["users"]:
            u = data["users"][user]
            hr_keys = ["bonus", "deductions", "overtime", "extra_leaves"]
            for key in hr_keys:
                if key not in u: u[key] = []
            if "salary" not in u: u["salary"] = 0.0
            if "hiring_date" not in u: u["hiring_date"] = "2024-01-01"
            if "role" not in u: u["role"] = "user"
            # خانات البيانات الشخصية الجديدة
            personal_keys = ["phone", "national_id", "address", "email", "social_status", "qualification"]
            for pk in personal_keys:
                if pk not in u: u[pk] = ""
        return data

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

# --- 2. Styling & Session Management ---
st.set_page_config(page_title="NMS ERP Ultimate", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # حفظ كل الحقول التي تبدأ بالرموز المخصصة لضمان عدم ضياع أي بيان
        draft_keys = ('s_','o_','e_','c_','m_','i_','ks','xs','op','u10','v22','ex','kj','xj','dn','k1','k2','x1','x2')
        draft_data = {k: v for k, v in st.session_state.items() if k.startswith(draft_keys)}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = draft_data
        save_db(db)

# --- 3. Login Section ---
if not st.session_state['logged_in']:
    st.title("🔐 NMS Enterprise Management")
    c1, c2 = st.columns(2)
    with c1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=300)
        else: st.info("Place Logo Here via Admin Settings")
    with c2:
        u_name = st.selectbox("Employee Account", list(db["users"].keys()))
        u_pass = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if db["users"][u_name]["pass"] == u_pass:
                st.session_state.update({'logged_in': True, 'user': u_name, 'role': db["users"][u_name]["role"]})
                # استعادة المسودة فور تسجيل الدخول
                if u_name in db.get("drafts", {}):
                    for key, val in db["drafts"][u_name].items(): st.session_state[key] = val
                db["logs"].append({"user": u_name, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Wrong Credentials")

else:
    # --- 4. Sidebar: THE COMPLETE ADMIN SUITE ---
    with st.sidebar:
        st.header(f"Hi, {db['users'][st.session_state['user']]['full_name']}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Master Control")
            admin_choice = st.selectbox("Menu", [
                "HR & Employee Profiles", 
                "Payroll & Development", 
                "Operational Tasks", 
                "Branches & Expenses", 
                "Archive & History"
            ])

            # 4.1 HR Profiles
            if admin_choice == "HR & Employee Profiles":
                st.write("### 👥 Manage Employees")
                target = st.selectbox("Select User", list(db["users"].keys()))
                u_profile = db["users"][target]
                
                with st.expander("Update All Details", expanded=True):
                    up_full = st.text_input("Full Name", value=u_profile.get('full_name', ''))
                    up_pass = st.text_input("Password", value=u_profile.get('pass', ''))
                    up_phone = st.text_input("Phone Number", value=u_profile.get('phone', ''))
                    up_nid = st.text_input("National ID", value=u_profile.get('national_id', ''))
                    up_addr = st.text_area("Home Address", value=u_profile.get('address', ''))
                    up_mail = st.text_input("Email", value=u_profile.get('email', ''))
                    up_stat = st.selectbox("Social Status", ["Single", "Married", "Divorced", "Other"], index=0)
                    up_qual = st.text_input("Educational Qualification", value=u_profile.get('qualification', ''))
                    if st.button("Save Full Profile"):
                        db["users"][target].update({
                            "full_name": up_full, "pass": up_pass, "phone": up_phone,
                            "national_id": up_nid, "address": up_addr, "email": up_mail,
                            "social_status": up_stat, "qualification": up_qual
                        })
                        save_db(db); st.success("Employee Profile Updated Successfully")
                
                st.divider()
                st.write("#### ➕ Create New Employee")
                new_un = st.text_input("Username (Unique)")
                if st.button("Create Account"):
                    if new_un and new_un not in db["users"]:
                        db["users"][new_un] = {
                            "pass": "123", "role": "user", "full_name": new_un,
                            "phone": "", "national_id": "", "address": "", "email": "",
                            "social_status": "Single", "qualification": "", "hiring_date": str(date.today()),
                            "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": []
                        }
                        save_db(db); st.success(f"Account '{new_un}' is now active."); st.rerun()

            # 4.2 Payroll
            elif admin_choice == "Payroll & Development":
                st.write("### 💰 Financial Development")
                target = st.selectbox("Select Staff", list(db["users"].keys()))
                u_fin = db["users"][target]
                
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    sal = st.number_input("Monthly Salary", value=float(u_fin.get('salary', 0)))
                with c_s2:
                    hire = st.date_input("Hiring Date", value=datetime.strptime(u_fin.get('hiring_date', "2024-01-01"), "%Y-%m-%d"))
                
                if st.button("Update Salary/Hire Date"):
                    db["users"][target]["salary"] = sal
                    db["users"][target]["hiring_date"] = str(hire)
                    save_db(db); st.success("HR Contract Saved")
                
                st.divider()
                dev_cat = st.radio("Add Financial Entry", ["Bonus", "Deduction", "Overtime", "Extra Leave"], horizontal=True)
                amt = st.number_input("Amount", step=10.0)
                note = st.text_area("Reason / Note")
                if st.button(f"Commit {dev_cat}"):
                    key = dev_cat.lower().replace(" ", "_")
                    db["users"][target][key].append({"date": str(date.today()), "val": amt, "note": note})
                    save_db(db); st.success("Recorded")

            # 4.3 Operational Tasks
            elif admin_choice == "Operational Tasks":
                st.write("### 📝 Edit Task Lists")
                t_cat = st.selectbox("Category", ["opening", "closing", "social", "interaction"])
                for i, t in enumerate(db["tasks"][t_cat]):
                    ct1, ct2 = st.columns([5, 1])
                    ct1.text(f"• {t}")
                    if ct2.button("🗑️", key=f"t_del_{t_cat}_{i}"):
                        db["tasks"][t_cat].pop(i); save_db(db); st.rerun()
                st.divider()
                nt = st.text_input("New Task Text")
                if st.button("Add Task"):
                    if nt: db["tasks"][t_cat].append(nt); save_db(db); st.rerun()

            # 4.4 Branches
            elif admin_choice == "Branches & Expenses":
                st.write("### 🏢 Manage Locations")
                for i, b in enumerate(db["branches"]):
                    st.text(f"Branch: {b}")
                st.divider()
                st.write("### 💸 Expense Categories")
                for i, e in enumerate(db["expense_categories"]):
                    ce1, ce2 = st.columns([5,1]); ce1.text(e)
                    if ce2.button("🗑️", key=f"ex_del_{i}"):
                        db["expense_categories"].pop(i); save_db(db); st.rerun()
                new_ex = st.text_input("New Expense Category")
                if st.button("Add Expense Cat"):
                    if new_ex: db["expense_categories"].append(new_ex); save_db(db); st.rerun()

            # 4.5 History
            elif admin_choice == "Archive & History":
                st.subheader("Shift Logs")
                if db["history"]: st.dataframe(pd.DataFrame(db["history"]))
                if st.button("Purge History", type="primary"): 
                    db["history"] = []; save_db(db); st.rerun()

    # --- 5. Main Content: DAILY OPERATIONS ---
    st.title("📊 NMS ERP - Professional Dashboard")
    m1, m2, m3, m4 = st.columns(4)
    with m1: branch = st.selectbox("Branch", db["branches"])
    with m2: shift = st.selectbox("Shift", ["Morning", "Night"])
    with m3: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    with m4: st.info(f"👤 User: {st.session_state['user']}")

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING & COUNTERS", "🔴 TAB 2: CLOSING & FINANCE", "📱 TAB 3: SOCIAL & SUMMARY"])

    # --- TAB 1: OPENING ---
    with tab1:
        st.subheader("Opening Procedures & Counters")
        c_o1, c_o2, c_o3 = st.columns([1, 1.5, 1.5])
        with c_o1:
            st.markdown("#### ✅ Tasks")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c_o2:
            st.markdown("#### 💵 Opening Cash")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Opening Coins", step=0.5, key="o_coins", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total Start: {t_open:,.2f}**")
        with c_o3:
            st.markdown("#### 🔢 Initial Counters")
            ks = st.number_input("Kyo Start Counter", step=1, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start Counter", step=1, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Balance Start", step=0.01, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit In (U10)", step=1.0, key="u10_val", on_change=sync_draft)

    # --- TAB 2: CLOSING ---
    with tab2:
        st.subheader("Shift Closing & Final Finance")
        c_c1, c_c2, c_c3 = st.columns([1, 1.5, 1.5])
        with c_c1:
            st.markdown("#### ✅ Tasks")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.markdown("#### 📱 System & Digital")
            sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales", on_change=sync_draft)
            insta = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wall = st.number_input("Wallet", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa", step=1.0, key="c_visa", on_change=sync_draft)
            v22 = st.number_input("Debit Out (V22)", step=1.0, key="v22_val", on_change=sync_draft)
            t_digital = insta + wall + visa
        with c_c2:
            st.markdown("#### 💵 Actual Cash Count")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, key="c_coins", on_change=sync_draft)
            t_close += c_coins
            st.divider()
            st.markdown("#### 💸 Expenses")
            ex_cat = st.selectbox("Category", db["expense_categories"], key="ex_cat")
            ex_val = st.number_input("Amount", step=1.0, key="ex_val")
            ex_note = st.text_input("Reason", key="ex_note")
            
            # THE CORE CALCULATION
            expected = t_open + sys_sales + u10 - ex_val - v22 - t_digital
            diff = t_close - expected
            st.metric("Expected Drawer", f"{expected:,.2f}")
            if abs(diff) < 0.1: st.success("Drawer Balanced")
            else: st.error(f"Drawer Diff: {diff:,.2f}")

        with c_c3:
            st.markdown("#### 🖨️ Detailed Printer Analysis")
            st.write("**Kyocera**")
            ke = st.number_input("Kyo End", step=1, key="ke")
            k1s = st.number_input("Kyo 1-Side", step=1, key="k1s_v")
            k2s = st.number_input("Kyo 2-Sides", step=1, key="k2s_v")
            kj = st.number_input("Kyo Jam / حشر ورق", step=1, key="kj_v", on_change=sync_draft)
            
            st.write("**Xerox**")
            xe = st.number_input("Xerox End", step=1, key="xe")
            x1s = st.number_input("Xerox 1-Side", step=1, key="x1s_v")
            x2s = st.number_input("Xerox 2-Sides", step=1, key="x2s_v")
            xj = st.number_input("Xerox Jam / حشر ورق", step=1, key="xj_v", on_change=sync_draft)
            
            st.divider()
            ope = st.number_input("Opay End Balance", step=0.01, key="ope")
            st.info(f"Opay Movement: {ops - ope:,.2f}")
            st.text_area("Notes / مسودة الملاحظات", key="dn_notes", on_change=sync_draft)

    # --- TAB 3: SOCIAL ---
    with tab3:
        st.subheader("Social Media & Shift Wrap-up")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("#### 📱 Marketing Tasks")
            for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        with sc2:
            st.markdown("#### 🤝 Interaction Tasks")
            for t in db["tasks"]["interaction"]: st.checkbox(t, key=f"i_{t}", on_change=sync_draft)
        
        st.divider()
        # WhatsApp Message Construction
        wa_text = f"*🚀 NMS COMPREHENSIVE REPORT*\n*Branch:* {branch} | *Staff:* {st.session_state['user']}\n\n" \
                  f"*💰 FINANCE:*\n- Sales: {sys_sales:,.2f}\n- Exp: {ex_val:,.2f} ({ex_cat})\n- Drawer: {t_close:,.2f}\n- Diff: {diff:,.2f}\n\n" \
                  f"*🖨️ PRINTERS:*\n- Kyo: {ke-ks} (Jam: {kj})\n- Xerox: {xe-xs} (Jam: {xj})\n\n" \
                  f"*💳 SYSTEM:*\n- Opay Move: {ops-ope:,.2f}\n- Debit V22: {v22:,.2f}"

        if st.button("🏁 ARCHIVE & COMMIT SHIFT", use_container_width=True):
            db["history"].append({
                "date": str(date.today()), "branch": branch, "staff": st.session_state['user'],
                "sales": sys_sales, "diff": diff, "kyo_jam": kj, "xerox_jam": xj
            })
            # Clear draft for this user after finish
            if st.session_state['user'] in db["drafts"]: del db["drafts"][st.session_state['user']]
            save_db(db); st.success("Shift Successfully Archived")

        crep1, crep2 = st.columns(2)
        with crep1:
            if st.button("📄 GENERATE DETAILED PDF", use_container_width=True):
                buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
                styles = getSampleStyleSheet(); parts = [Paragraph(f"NMS Shift Report - {branch} - {date.today()}", styles['Title'])]
                p_data = [
                    ["Field", "Detail"], ["Staff", st.session_state['user']], 
                    ["Sales", sys_sales], ["Expenses", f"{ex_val} ({ex_note})"],
                    ["Difference", diff], ["Kyo Total", ke-ks], ["Xerox Total", xe-xs]
                ]
                tbl = Table(p_data, colWidths=[200, 300])
                tbl.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
                parts.append(tbl); doc.build(parts)
                st.download_button("📥 Download PDF", buf.getvalue(), f"NMS_Report_{date.today()}.pdf")
        with crep2:
            url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 WHATSAPP FULL REPORT</button></a>', unsafe_allow_html=True)
