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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# --- 1. إعدادات قاعدة البيانات (Database Configuration) ---
DB_FILE = 'nms_enterprise_pro_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    # الهيكل الافتراضي الكامل (لضمان عدم حدوث أخطاء)
    default_structure = {
        "logo": None,
        "branches": ["M. Nageb Branch", "Tram Branch"],
        "expense_categories": ["Electricity", "Water", "Maintenance", "Supplies", "Salary Advance", "Rent", "Other"],
        "users": {
            "admin": {
                "pass": "admin123", "role": "admin", "full_name": "Manager",
                "phone": "", "national_id": "", "address": "", "email": "",
                "social_status": "Single", "qualification": "", "hiring_date": "2024-01-01",
                "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": [], "photo": None
            }
        },
        "tasks": {
            "opening": [
                "Fingerprint Attendance 👆", "Power On Devices 🔌", "Uniform & Name Tag 👔", 
                "Music & Ambience 🎶", "Paper Loaded 📄", "Cash Counted 💵", 
                "Clean Windows & Counters 🧹", "Check Internet Connection 🌐", "Check Supplies Inventory 📦"
            ],
            "closing": [
                "Save WhatsApp Contacts 📱", "Cleaning Workplace 🧹", 
                "Power Off Devices 🔌", "Trash Removed 🗑️", "Fingerprint Sign-out 👆", 
                "Daily Report Sent 📩", "Safe Locked 🔒", "Lights Off 💡"
            ],
            "social": [
                "Canva Design 1 🎨", "Canva Design 2 🎨", "WhatsApp Story 🟢", "WhatsApp Channel 📢", 
                "Facebook Account Story 🔵", "Facebook Account Post/Reel 🎬", "Facebook Account Group 👥", 
                "Facebook Page Story 📄", "Facebook Page Post/Reel 🎬", "Threads Post 🧵", 
                "Instagram Story 📸", "Instagram Post/Reel 🎥", "TikTok Story 🎵", "TikTok Post 🕺", 
                "Telegram Story ✈️", "Telegram Channel 📢", "LinkedIn Post 💼"
            ],
            "interaction": [
                "Like 👍", "Love ❤️", "Care 🤗", "Share 🔗", 
                "Comment 💬", "Reply to Messages 📩", "Join Groups 👥"
            ]
        },
        "history": [], "drafts": {}, "logs": []
    }
    
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return default_structure
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # إصلاح وتحديث بيانات المستخدمين القدامى لضمان عدم حدوث أخطاء
        for user in data["users"]:
            u = data["users"][user]
            # التأكد من وجود خانات الـ HR
            hr_keys = ["bonus", "deductions", "overtime", "extra_leaves"]
            for key in hr_keys:
                if key not in u: u[key] = []
            if "salary" not in u: u["salary"] = 0.0
            if "hiring_date" not in u: u["hiring_date"] = "2024-01-01"
            if "role" not in u: u["role"] = "user"
            if "photo" not in u: u["photo"] = None
            # التأكد من وجود البيانات الشخصية
            personal_keys = ["phone", "national_id", "address", "email", "social_status", "qualification"]
            for pk in personal_keys:
                if pk not in u: u[pk] = ""
        # التأكد من وجود أقسام المهام
        if "tasks" not in data: data["tasks"] = default_structure["tasks"]
        for cat in default_structure["tasks"]:
            if cat not in data["tasks"]: data["tasks"][cat] = default_structure["tasks"][cat]
            
        return data

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

# --- 2. Advanced PDF Generation (تقرير شامل) ---
def create_downloadable_pdf(branch, staff_name, date_str, sales, expenses, exp_note, diff, kyo_data, xerox_data, opay_move, debit_v22):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # تنسيقات مخصصة
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=20, textColor=colors.darkblue)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=12, alignment=1, spaceAfter=30)
    
    # 1. الترويسة (لوجو + صورة الموظف)
    logo_img = None
    staff_img = None
    
    if db.get("logo"):
        try:
            logo_bytes = base64.b64decode(db["logo"])
            logo_img = Image(io.BytesIO(logo_bytes), width=1.5*inch, height=1.5*inch)
        except: pass

    staff_data = db["users"].get(st.session_state['user'], {})
    if staff_data.get("photo"):
        try:
            staff_bytes = base64.b64decode(staff_data["photo"])
            staff_img = Image(io.BytesIO(staff_bytes), width=1.2*inch, height=1.2*inch)
        except: pass

    header_data = [[logo_img if logo_img else "", Paragraph(f"<b>NMS ENTERPRISE REPORT</b><br/>{branch}", title_style), staff_img if staff_img else ""]]
    header_table = Table(header_data, colWidths=[2*inch, 6*inch, 2*inch])
    header_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Date: {date_str} | Generated By: {staff_name}", sub_style))

    # 2. الجدول المالي
    elements.append(Paragraph("💰 Financial Summary", styles['Heading2']))
    fin_data = [
        ["Item", "Value", "Notes"],
        ["Total Sales", f"{sales:,.2f}", "-"],
        ["Expenses", f"{expenses:,.2f}", exp_note],
        ["Opay Movement", f"{opay_move:,.2f}", "-"],
        ["Debit (V22)", f"{debit_v22:,.2f}", "Postponed"],
        ["NET DIFFERENCE", f"{diff:,.2f}", "Final Status"]
    ]
    fin_table = Table(fin_data, colWidths=[2.5*inch, 2.5*inch, 4*inch])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,5), (-1,5), colors.lightgrey),
        ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold'),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 20))

    # 3. جدول الطابعات
    elements.append(Paragraph("🖨️ Printers Analysis", styles['Heading2']))
    prn_data = [
        ["Machine", "Total Used", "Paper Jam", "1-Sided", "2-Sided"],
        ["Kyocera", kyo_data['used'], kyo_data['jam'], kyo_data['1s'], kyo_data['2s']],
        ["Xerox", xerox_data['used'], xerox_data['jam'], xerox_data['1s'], xerox_data['2s']]
    ]
    prn_table = Table(prn_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 2*inch, 2*inch])
    prn_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkred),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(prn_table)

    doc.build(elements)
    return buffer.getvalue()

# --- 3. Session Setup ---
st.set_page_config(page_title="NMS ERP Platinum", layout="wide", page_icon="🚀")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        draft_keys = ('s_','o_','e_','c_','m_','i_','ks','xs','op','u10','v22','ex','kj','xj','dn','k1','k2','x1','x2')
        draft_data = {k: v for k, v in st.session_state.items() if k.startswith(draft_keys)}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = draft_data
        save_db(db)

# --- 4. Login Screen ---
if not st.session_state['logged_in']:
    st.title("🔐 NMS Enterprise Access")
    c1, c2 = st.columns(2)
    with c1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=350)
        else: st.info("ℹ️ Upload Company Logo in Admin Panel")
    with c2:
        st.write("### 🔑 Secure Login")
        u = st.selectbox("Select Your Account", list(db["users"].keys()))
        p = st.text_input("Enter Password", type="password")
        if st.button("🚀 Login", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items(): st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("❌ Access Denied")

else:
    # --- 5. Sidebar System ---
    with st.sidebar:
        user_info = db["users"][st.session_state['user']]
        if user_info.get("photo"): 
            st.image(base64.b64decode(user_info["photo"]), width=120)
        else:
            st.write("👤 No Photo")
            
        st.header(f"Hi, {user_info['full_name']}")
        
        # --- بوابة الموظف (Self-Service) ---
        if st.session_state['role'] == 'user':
            st.divider()
            st.subheader("📂 My Financial Profile")
            st.write(f"**📅 Hiring Date:** {user_info.get('hiring_date', '-')}")
            st.metric("💰 Base Salary", f"{user_info.get('salary', 0):,.2f} LE")
            
            with st.expander("🎁 My Bonuses", expanded=False):
                if user_info['bonus']: st.dataframe(pd.DataFrame(user_info['bonus']))
                else: st.info("No bonuses yet.")
                    
            with st.expander("⏳ Overtime", expanded=False):
                if user_info['overtime']: st.dataframe(pd.DataFrame(user_info['overtime']))
                else: st.info("No overtime yet.")
                    
            with st.expander("⚠️ My Deductions", expanded=False):
                if user_info['deductions']: st.dataframe(pd.DataFrame(user_info['deductions']))
                else: st.success("Clean Record! No deductions.")
                    
            with st.expander("🏖️ Extra Leave", expanded=False):
                if user_info['extra_leaves']: st.dataframe(pd.DataFrame(user_info['extra_leaves']))
                else: st.success("Clean Record! No extra_leaves.")
                    
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        
        # --- صلاحيات المدير المطلقة (Master Control) ---
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ Admin Authority")
            admin_choice = st.selectbox("Select Management Module:", [
                "👥 Manage Employees (HR)", 
                "💰 Payroll & Money", 
                "📝 Tasks & Checklists", 
                "🏢 Branches & Expenses", 
                "📂 Archive & History"
            ])

            # 1. إدارة الموظفين (HR)
            if admin_choice == "👥 Manage Employees (HR)":
                st.info("Edit, Delete, or Add Employees")
                target = st.selectbox("Select Employee to Edit", list(db["users"].keys()))
                u_prof = db["users"][target]
                
                with st.expander("📸 Update Photo", expanded=False):
                    new_pic = st.file_uploader("Upload Photo", type=['png','jpg'])
                    if st.button("Save Photo"):
                        if new_pic:
                            db["users"][target]["photo"] = base64.b64encode(new_pic.getvalue()).decode()
                            save_db(db); st.success("Photo Updated!"); st.rerun()

                with st.expander("📝 Edit Personal Details", expanded=True):
                    up_full = st.text_input("Full Name", value=u_prof.get('full_name', ''))
                    up_pass = st.text_input("Password", value=u_prof.get('pass', ''))
                    up_phone = st.text_input("Phone Number", value=u_prof.get('phone', ''))
                    up_email = st.text_input("E-Mail", value=u_prof.get('email', ''))                    
                    up_nid = st.text_input("National ID", value=u_prof.get('national_id', ''))
                    up_addr = st.text_area("Address", value=u_prof.get('address', ''))
                    up_qual = st.text_input("Qualification", value=u_prof.get('qualification', ''))
                    if st.button("💾 Save Changes"):
                        db["users"][target].update({
                            "full_name": up_full, "pass": up_pass, "phone": up_phone,
                            "national_id": up_nid, "address": up_addr, "qualification": up_qual
                        })
                        save_db(db); st.success("Saved")
                
                # زر حذف الموظف
                if target != 'admin':
                    if st.button("🗑️ Delete This Employee", type="primary"):
                        del db["users"][target]
                        save_db(db); st.warning(f"User {target} Deleted!"); st.rerun()
                
                st.write("---")
                st.write("#### ➕ Add New Employee")
                new_u = st.text_input("New Username")
                if st.button("Create Account"):
                    if new_u and new_u not in db["users"]:
                        db["users"][new_u] = {
                            "pass": "123", "role": "user", "full_name": new_u,
                            "salary": 0.0, "bonus": [], "deductions": [], "overtime": [], "extra_leaves": [], "photo": None, "hiring_date": str(date.today()),
                            "phone": "", "national_id": "", "address": "", "qualification": ""
                        }
                        save_db(db); st.success("Created"); st.rerun()

            # 2. الرواتب والماليات
            elif admin_choice == "💰 Payroll & Money":
                st.info("Manage Salaries, Bonuses & Deductions")
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                u_fin = db["users"][target]
                
                col_s1, col_s2 = st.columns(2)
                with col_s1: sal = st.number_input("Base Salary", value=float(u_fin.get('salary', 0)))
                with col_s2: hire = st.date_input("Hiring Date", value=datetime.strptime(u_fin.get('hiring_date', "2024-01-01"), "%Y-%m-%d"))
                if st.button("💾 Update Contract"):
                    db["users"][target]["salary"] = sal
                    db["users"][target]["hiring_date"] = str(hire)
                    save_db(db); st.success("Contract Updated")
                
                st.divider()
                st.write("**Add Financial Entry:**")
                dev_type = st.radio("Type", ["Bonus 🎁", "Deductions ⚠️", "Overtime ⏳", "Extra Leave 🏖️"], horizontal=True)
                amt = st.number_input("Value (LE)", step=10.0)
                note = st.text_input("Reason / Note")
                if st.button("✅ Submit Entry"):
                    key = dev_type.split()[0].lower()
                    if key == "extra": key = "extra_leaves"
                    db["users"][target][key].append({"date": str(date.today()), "val": amt, "note": note})
                    save_db(db); st.success("Added to HR Record")

            # 3. إدارة المهام
            elif admin_choice == "📝 Tasks & Checklists":
                cat = st.selectbox("Category", ["opening", "closing", "social", "interaction"])
                for i, t in enumerate(db["tasks"][cat]):
                    c1, c2 = st.columns([5, 1])
                    c1.text(f"📌 {t}")
                    if c2.button("🗑️", key=f"del_t_{cat}_{i}"):
                        db["tasks"][cat].pop(i); save_db(db); st.rerun()
                new_t = st.text_input("New Task")
                if st.button("➕ Add Task"):
                    if new_t: db["tasks"][cat].append(new_t); save_db(db); st.rerun()
                        
            # 4. الفروع والمصاريف
            elif admin_choice == "🏢 Branches & Expenses":
                st.info("Manage Locations & Expenses")
                
                st.write("**🏢 Branches (الفروع)**")
                br_sel = st.selectbox("Select Branch", db["branches"])
                c_br1, c_br2 = st.columns(2)
                with c_br1:
                    new_br_name = st.text_input("Rename Branch", value=br_sel)
                    if st.button("✏️ Rename"):
                        idx = db["branches"].index(br_sel)
                        db["branches"][idx] = new_br_name
                        save_db(db); st.success("Renamed!"); st.rerun()
                with c_br2:
                    if st.button("🗑️ Delete Branch", type="primary"):
                        db["branches"].remove(br_sel)
                        save_db(db); st.warning("Deleted!"); st.rerun()
                
                new_b_add = st.text_input("New Branch Name")
                if st.button("➕ Create Branch"):
                    if new_b_add: db["branches"].append(new_b_add); save_db(db); st.rerun()

                st.divider()
                st.write("**💸 Expense Categories (بنود المصاريف)**")
                for i, e in enumerate(db["expense_categories"]):
                    ce1, ce2 = st.columns([5,1]); ce1.text(f"🔹 {e}")
                    if ce2.button("✖️", key=f"del_ex_{i}"): db["expense_categories"].pop(i); save_db(db); st.rerun()
                new_ex = st.text_input("New Expense Category")
                if st.button("➕ Add Expense Category"):
                    if new_ex: db["expense_categories"].append(new_ex); save_db(db); st.rerun()

            # 5. الأرشيف
            elif admin_choice == "📂 Archive & History":
                st.subheader("📜 Shift Logs")
                if db["history"]: st.dataframe(pd.DataFrame(db["history"]))
                if st.button("⚠️ Clear All History", type="primary"): 
                    db["history"] = []; save_db(db); st.rerun()
                
                st.divider()
                lg = st.file_uploader("Upload Company Logo", type=['png', 'jpg'])
                if st.button("💾 Save Logo"):
                    if lg: 
                        db["logo"] = base64.b64encode(lg.getvalue()).decode()
                        save_db(db); st.success("Logo Updated"); st.rerun()

    # --- 6. Main Dashboard: DAILY OPERATIONS ---
    st.title("📊 NMS ERP - Daily Operations")
    m1, m2, m3, m4 = st.columns(4)
    with m1: branch = st.selectbox("📍 Branch", db["branches"])
    with m2: shift = st.selectbox("🕒 Shift", ["Morning", "Between", "Night"])
    with m3: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    with m4: st.info(f"👤 {st.session_state['user']}")

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])

    # --- TAB 1: OPENING ---
    with tab1:
        st.subheader("🌅 Opening Procedures")
        c_o1, c_o2, c_o3 = st.columns([1, 1.5, 1.5])
        with c_o1:
            st.markdown("#### ✅ Opening Tasks")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c_o2:
            st.markdown("#### 💵 Cash Denominations (Opening)")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Coins", step=0.5, key="o_coins", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total Opening: {t_open:,.2f} LE**")
        with c_o3:
            st.markdown("#### 🔢 Initial Counters")
            ks = st.number_input("Kyocera Start", step=1, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Start Balance", step=0.01, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit", step=1.0, key="u10_val", on_change=sync_draft)

    # --- TAB 2: CLOSING ---
    with tab2:
        st.subheader("🌇 Closing Procedures")
        c_c1, c_c2, c_c3 = st.columns([1, 1.5, 1.5])
        with c_c1:
            st.markdown("#### ✅ Closing Tasks")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.markdown("#### 💳 System & Payments")
            sys_sales = st.number_input("💻 System Sales", step=1.0, key="c_sys_sales", on_change=sync_draft)
            insta = st.number_input("📱 Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wall = st.number_input("👛 Wallet (VF/Etisalat)", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("💳 Visa", step=1.0, key="c_visa", on_change=sync_draft)
            v22 = st.number_input("📉 Debit", step=1.0, key="v22_val", on_change=sync_draft)
            t_digital = insta + wall + visa
        with c_c2:
            st.markdown("#### 💵 Cash Denominations (Closing)")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, key="c_coins", on_change=sync_draft)
            t_close += c_coins
            
            st.divider()
            st.markdown("#### 💸 Expenses Detail")
            ex_cat = st.selectbox("Category", db["expense_categories"], key="ex_cat")
            ex_val = st.number_input("Amount", step=1.0, key="ex_val")
            ex_note = st.text_input("Details / Reason", key="ex_note")
            
            # CORE MATH
            expected = t_open + sys_sales + u10 - ex_val - v22 - t_digital
            diff = t_close - expected
            st.metric("Expected Drawer", f"{expected:,.2f} LE")
            if abs(diff) < 0.1: st.success("✨ Perfect Match!")
            elif diff > 0: st.warning(f"➕ Surplus: {diff:,.2f}")
            else: st.error(f"➖ Shortage: {diff:,.2f}")

        with c_c3:
            st.markdown("#### 🖨️ Printers Detail")
            st.info("Kyocera")
            ke = st.number_input("Kyo End", step=1, key="ke")
            k1s = st.number_input("1-Sided", step=1, key="k1s_v")
            k2s = st.number_input("2-Sided", step=1, key="k2s_v")
            kj = st.number_input("⚠️ Paper Jam", step=1, key="kj_v", on_change=sync_draft)
            
            st.info("Xerox")
            xe = st.number_input("Xerox End", step=1, key="xe")
            x1s = st.number_input("1-Sided", step=1, key="x1s_v")
            x2s = st.number_input("2-Sided", step=1, key="x2s_v")
            xj = st.number_input("⚠️ Paper Jam", step=1, key="xj_v", on_change=sync_draft)
            
            st.divider()
            ope = st.number_input("Opay End Balance", step=0.01, key="ope")
            st.write(f"📉 Opay Used: {ops - ope:,.2f}")
            
            st.text_area("📝 Draft Notes / Handover", key="dn_notes", on_change=sync_draft)

    # --- TAB 3: SOCIAL ---
    with tab3:
        st.subheader("📱 Marketing & Finalization")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("#### 📢 Social Media Tasks")
            for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        with sc2:
            st.markdown("#### ❤️ Interaction Tasks")
            for t in db["tasks"]["interaction"]: st.checkbox(t, key=f"i_{t}", on_change=sync_draft)
        
        st.divider()
        st.write("### 🏁 End Shift Actions")
        
--- تحديث بناء نص رسالة واتساب (WhatsApp Construction) ---

    # 1. حساب المهام المنجزة
    def count_tasks(prefix):
        total = len([k for k in st.session_state if k.startswith(prefix)])
        done = len([k for k in st.session_state if k.startswith(prefix) and st.session_state[k]])
        return done, total

    op_done, op_tot = count_tasks('s_')
    cl_done, cl_tot = count_tasks('e_')
    soc_done, soc_tot = count_tasks('m_')
    int_done, int_tot = count_tasks('i_')

    # 2. تجميع ملاحظات الأخطاء والفروقات
    error_notes = []
    if abs(diff) > 0.1:
        error_notes.append(f"⚠️ فرق نقدية: {diff:,.2f}")
    
    # فرق طابعات (إذا كان الاستخدام الفعلي لا يساوي مجموع الـ 1s والـ 2s)
    kyo_actual = ke - ks
    kyo_reported = k1s + k2s
    if kyo_actual != kyo_reported:
        error_notes.append(f"⚠️ فرق عداد كيوسيرا: الفعلي {kyo_actual} والمسجل {kyo_reported}")
        
    xerox_actual = xe - xs
    xerox_reported = x1s + x2s
    if xerox_actual != xerox_reported:
        error_notes.append(f"⚠️ فرق عداد زيروكس: الفعلي {xerox_actual} والمسجل {xerox_reported}")

    notes_section = "\n".join(error_notes) if error_notes else "✅ لا توجد فروقات حسابية"

    # 3. بناء نص الرسالة الشامل
    wa_text = f"*🚀 NMS ERP - تقرير وردية شامل*\n" \
              f"━━━━━━━━━━━━━━━━\n" \
              f"📅 التاريخ: {date.today()}\n" \
              f"👤 الاسم: {st.session_state['user']}\n" \
              f"📍 الفرع: {branch}\n" \
              f"🕒 الوردية: {shift}\n\n" \
              f"*💰 الملخص المالي*\n" \
              f"━━━━━━━━━━━━━━━━\n" \
              f"💵 نقدية البداية: {t_open:,.2f}\n" \
              f"💻 مبيعات السيستم: {sys_sales:,.2f}\n" \
              f"💸 المصاريف: {ex_val:,.2f} ({ex_cat}: {ex_note})\n" \
              f"💳 مدفوعات أونلاين: {t_digital:,.2f}\n" \
              f"   (فودافون: {wall} | إنستا: {insta} | فيزا: {visa})\n" \
              f"📉 آجل (V22): {v22:,.2f}\n" \
              f"💰 نقدية النهاية: {t_close:,.2f}\n" \
              f"⚖️ فرق العجز/الزيادة: {diff:,.2f}\n\n" \
              f"*🖨️ تقرير الطابعات*\n" \
              f"━━━━━━━━━━━━━━━━\n" \
              f"📠 كيوسيرا: {kyo_actual} (حشر: {kj})\n" \
              f"📠 زيروكس: {xerox_actual} (حشر: {xj})\n" \
              f"📱 فرق أوباي: {ops-ope:,.2f}\n\n" \
              f"*✅ إحصائيات المهام*\n" \
              f"━━━━━━━━━━━━━━━━\n" \
              f"🌅 مهام الافتتاح: {op_done}/{op_tot}\n" \
              f"🌇 مهام الإغلاق: {cl_done}/{cl_tot}\n" \
              f"📱 السوشيال ميديا: {soc_done}/{soc_tot}\n" \
              f"🤝 التفاعل: {int_done}/{int_tot}\n\n" \
              f"*📝 ملاحظات وفروقات*\n" \
              f"━━━━━━━━━━━━━━━━\n" \
              f"{notes_section}\n" \
              f"📌 ملاحظات الوردية: {st.session_state.get('dn_notes', '-')}"

    # --- زر الأرشفة والأزرار النهائية ---
    if st.button("💾 ARCHIVE SHIFT & DATA", use_container_width=True):
        db["history"].append({
            "date": str(date.today()), "branch": branch, "staff": st.session_state['user'],
            "sales": sys_sales, "diff": diff, "kyo_jam": kj, "xerox_jam": xj, "expenses": ex_val,
            "exp_note": f"{ex_cat}: {ex_note}"
        })
        if st.session_state['user'] in db["drafts"]: del db["drafts"][st.session_state['user']]
        save_db(db); st.success("Shift Archived Successfully!")

    crep1, crep2 = st.columns(2)
    with crep1:
        if st.button("📄 GENERATE PRO PDF", use_container_width=True):
            kyo_d = {'used': ke-ks, 'jam': kj, '1s': k1s, '2s': k2s}
            xerox_d = {'used': xe-xs, 'jam': xj, '1s': x1s, '2s': x2s}
            pdf_bytes = create_downloadable_pdf(branch, st.session_state['user'], str(date.today()), sys_sales, ex_val, f"{ex_cat}: {ex_note}", diff, kyo_d, xerox_d, ops-ope, v22)
            st.download_button("📥 Download Official Report", pdf_bytes, f"NMS_Pro_{date.today()}.pdf")
    with crep2:
        url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold; font-size:16px;">📱 SEND TO WHATSAPP</button></a>', unsafe_allow_html=True)
