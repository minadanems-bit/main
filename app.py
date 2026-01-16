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
                "opening": ["Fingerprint", "Power On", "Uniform", "Cash Counted"],
                "closing": ["Cleaned", "Power Off", "Report Sent"],
                "social": ["Facebook", "Instagram", "WhatsApp"],
                "interaction": ["Like", "Share", "Comment"]
            },
            "history": [],
            "drafts": {},
            "logs": []
        }
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

# --- 2. Setup & Session ---
st.set_page_config(page_title="NMS ERP Pro", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # Capture all input keys
        draft_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_','o_','e_','c_','m_','i_','ks','xs','op','u10','v22','ex'))}
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
        u = st.selectbox("Employee Name", list(db["users"].keys()))
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
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
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
        
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Master Admin Suite")
            admin_choice = st.selectbox("Select Management Area", [
                "HR & Employee Profiles", 
                "Payroll & Development", 
                "Tasks Management", 
                "Branches & Expenses", 
                "Archives & Logs"
            ])

            # 4.1 HR & PROFILES
            if admin_choice == "HR & Employee Profiles":
                st.write("### 👤 Employee Database")
                target = st.selectbox("Select Account", list(db["users"].keys()))
                u_data = db["users"][target]
                
                with st.expander("Edit Personal Information", expanded=False):
                    u_full = st.text_input("Full Name", value=u_data.get('full_name', ''))
                    u_pass = st.text_input("Password", value=u_data.get('pass', ''))
                    u_phone = st.text_input("Phone Number", value=u_data.get('phone', ''))
                    u_nid = st.text_input("National ID", value=u_data.get('national_id', ''))
                    u_addr = st.text_area("Address", value=u_data.get('address', ''))
                    u_mail = st.text_input("Email", value=u_data.get('email', ''))
                    u_stat = st.selectbox("Social Status", ["Single", "Married", "Other"], index=0)
                    u_qual = st.text_input("Qualification", value=u_data.get('qualification', ''))
                    if st.button("Save Profile Update"):
                        db["users"][target].update({
                            "full_name": u_full, "pass": u_pass, "phone": u_phone,
                            "national_id": u_nid, "address": u_addr, "email": u_mail,
                            "social_status": u_stat, "qualification": u_qual
                        })
                        save_db(db); st.success("Profile Updated")
                
                if st.button("➕ Add New Employee"):
                    new_id = st.text_input("New Username")
                    if new_id and new_id not in db["users"]:
                        db["users"][new_id] = {"pass": "123", "role": "user", "full_name": new_id, "bonus":[], "deductions":[], "overtime":[], "extra_leaves":[]}
                        save_db(db); st.rerun()

            # 4.2 PAYROLL & DEVELOPMENT
            elif admin_choice == "Payroll & Development":
                st.write("### 💰 Financial & HR Development")
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                u_fin = db["users"][target]
                
                c_a, c_b = st.columns(2)
                with c_a:
                    new_sal = st.number_input("Base Salary", value=float(u_fin.get('salary', 0)))
                    hire_dt = st.date_input("Hiring Date", value=datetime.strptime(u_fin.get('hiring_date', "2024-01-01"), "%Y-%m-%d"))
                with c_b:
                    st.write("Actions")
                    if st.button("Update Contract Info"):
                        db["users"][target]["salary"] = new_sal
                        db["users"][target]["hiring_date"] = str(hire_dt)
                        save_db(db); st.success("Saved")

                st.divider()
                dev_type = st.radio("Add Record", ["Bonus", "Deduction", "Overtime", "Extra Leave"], horizontal=True)
                d_amt = st.number_input("Amount / Value", step=10.0)
                d_reason = st.text_area("Reason / Description")
                if st.button(f"Add {dev_type}"):
                    key = dev_type.lower().replace(" ", "_")
                    if key not in db["users"][target]: db["users"][target][key] = []
                    db["users"][target][key].append({"date": str(date.today()), "val": d_amt, "note": d_reason})
                    save_db(db); st.success("Added to HR File")

            # 4.3 TASKS MANAGEMENT (Restored & Enhanced)
            elif admin_choice == "Tasks Management":
                st.write("### 📋 Edit Operational Tasks")
                t_cat = st.selectbox("Category", ["opening", "closing", "social", "interaction"])
                for i, t in enumerate(db["tasks"][t_cat]):
                    col_t1, col_t2 = st.columns([4, 1])
                    col_t1.text(f"• {t}")
                    if col_t2.button("🗑️", key=f"dt_{t_cat}_{i}"):
                        db["tasks"][t_cat].pop(i); save_db(db); st.rerun()
                nt = st.text_input("New Task Name")
                if st.button("Add Task"):
                    if nt: db["tasks"][t_cat].append(nt); save_db(db); st.rerun()

            # 4.4 BRANCHES & EXPENSES
            elif admin_choice == "Branches & Expenses":
                st.write("### 🏢 Branches")
                for i, b in enumerate(db["branches"]):
                    cb1, cb2 = st.columns([4,1]); cb1.text(b)
                    if cb2.button("🗑️", key=f"br_{i}"): db["branches"].pop(i); save_db(db); st.rerun()
                nb = st.text_input("New Branch")
                if st.button("Add Branch"): db["branches"].append(nb); save_db(db); st.rerun()
                
                st.divider()
                st.write("### 💸 Expense Categories")
                for i, e in enumerate(db["expense_categories"]):
                    ce1, ce2 = st.columns([4,1]); ce1.text(e)
                    if ce2.button("🗑️", key=f"ex_{i}"): db["expense_categories"].pop(i); save_db(db); st.rerun()
                ne = st.text_input("New Expense Category")
                if st.button("Add Category"): db["expense_categories"].append(ne); save_db(db); st.rerun()

            # 4.5 ARCHIVES & LOGS
            elif admin_choice == "Archives & Logs":
                st.subheader("📜 System Audit")
                if st.checkbox("Show Login Logs"): st.table(db["logs"][-20:])
                st.write("### Shift History")
                if db["history"]:
                    st.dataframe(pd.DataFrame(db["history"]))
                    if st.button("Clear History", type="primary"): db["history"] = []; save_db(db); st.rerun()

    # --- 5. Main Content: DAILY OPERATIONS ---
    st.title("🚀 NMS Enterprise - Daily Operations")
    m1, m2, m3, m4 = st.columns(4)
    with m1: branch = st.selectbox("Branch Location", db["branches"])
    with m2: shift = st.selectbox("Shift Type", ["Morning", "Afternoon", "Night"])
    with m3: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    with m4: st.info(f"👤 User: {st.session_state['user']}")

    tab1, tab2, tab3 = st.tabs(["🟢 TAB 1: OPENING & COUNTERS", "🔴 TAB 2: CLOSING & FINANCE", "📱 TAB 3: SOCIAL & ARCHIVE"])

    # --- TAB 1: OPENING ---
    with tab1:
        st.subheader("Shift Start Checklist & Initial State")
        col_o1, col_o2, col_o3 = st.columns([1, 1.5, 1.5])
        with col_o1:
            st.markdown("#### ✅ Opening Tasks")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with col_o2:
            st.markdown("#### 💵 Opening Cash (Drawer)")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (v * d)
            o_coins = st.number_input("Opening Coins", step=0.5, key="o_coins", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total Opening Cash: {t_open:,.2f}**")
        with col_o3:
            st.markdown("#### 🔢 Start Counters & Debt")
            ks = st.number_input("Kyocera Start Counter", step=1, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start Counter", step=1, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Balance Start", step=0.01, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit Received (U10)", step=1.0, key="u10_val", on_change=sync_draft)

    # --- TAB 2: CLOSING ---
    with tab2:
        st.subheader("Shift End Operations & Full Financials")
        col_c1, col_c2, col_c3 = st.columns([1, 1.5, 1.5])
        with col_c1:
            st.markdown("#### ✅ Closing Tasks")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            st.markdown("#### 💻 System & Payments")
            sys_sales = st.number_input("System Sales Total", step=1.0, key="c_sys_sales", on_change=sync_draft)
            instapay = st.number_input("Instapay Received", step=1.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallets (VF/Etisalat)", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa / Credit Card", step=1.0, key="c_visa", on_change=sync_draft)
            v22 = st.number_input("Debit Postponed (V22)", step=1.0, key="v22_val", on_change=sync_draft)
            t_digital = instapay + wallet + visa
        with col_c2:
            st.markdown("#### 💵 Closing Cash (Actual)")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (v * d)
            c_coins = st.number_input("Closing Coins ", step=0.5, key="c_coins", on_change=sync_draft)
            t_close += c_coins
            
            st.divider()
            st.markdown("#### 💸 Expenses Detail")
            ex_cat = st.selectbox("Expense Category", db["expense_categories"], key="ex_cat")
            ex_val = st.number_input("Expense Amount", step=1.0, key="ex_val")
            ex_note = st.text_input("Expense Reason / Details", key="ex_note")
            
            # FINANCIAL LOGIC
            expected = t_open + sys_sales + u10 - ex_val - v22 - t_digital
            diff = t_close - expected
            st.metric("Expected Drawer Cash", f"{expected:,.2f}")
            if abs(diff) < 0.1: st.success("Balance Perfect!")
            else: st.error(f"Drawer Difference: {diff:,.2f}")

        with col_c3:
            st.markdown("#### 🖨️ Detailed Printer Analysis")
            st.write("**Kyocera**")
            ke = st.number_input("Kyocera End Counter", step=1, key="ke")
            k_one = st.number_input("Kyo One-Side Only", step=1, key="k_one")
            k_two = st.number_input("Kyo Two-Sided (Duplex)", step=1, key="k_two")
            
            st.write("**Xerox**")
            xe = st.number_input("Xerox End Counter", step=1, key="xe")
            x_one = st.number_input("Xerox One-Side Only", step=1, key="x_one")
            x_two = st.number_input("Xerox Two-Sided (Duplex)", step=1, key="x_two")
            
            st.divider()
            st.write("**Opay**")
            ope = st.number_input("Opay Balance End", step=0.01, key="ope")
            st.info(f"Opay Movement: {ops - ope:,.2f}")

    # --- TAB 3: SOCIAL & ARCHIVE ---
    with tab3:
        st.subheader("Marketing, Interaction & Shift Export")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("#### 📱 Social Media Tasks")
            for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        with sc2:
            st.markdown("#### 🤝 Interaction Tasks")
            for t in db["tasks"]["interaction"]: st.checkbox(t, key=f"i_{t}", on_change=sync_draft)

        st.divider()
        st.subheader("🏁 Final Submission")
        
        # WhatsApp Message Construction
        wa_text = f"*🚀 NMS FULL SHIFT REPORT*\n" \
                  f"*Branch:* {branch} | *Staff:* {st.session_state['user']}\n" \
                  f"*Shift:* {shift}\n\n" \
                  f"*💰 FINANCE:*\n" \
                  f"- Sales: {sys_sales:,.2f}\n" \
                  f"- Expenses: {ex_val:,.2f} ({ex_cat}: {ex_note})\n" \
                  f"- Digital (Insta/Visa/Wall): {t_digital:,.2f}\n" \
                  f"- Drawer Actual: {t_close:,.2f}\n" \
                  f"- Difference: {diff:,.2f}\n\n" \
                  f"*🖨️ PRINTERS (Kyo | Xerox):*\n" \
                  f"- Kyo Used: {ke-ks} (1S: {k_one}, 2S: {k_two})\n" \
                  f"- Xerox Used: {xe-xs} (1S: {x_one}, 2S: {x_two})\n\n" \
                  f"*💳 SYSTEMS:*\n" \
                  f"- Opay Change: {ops-ope:,.2f}\n" \
                  f"- Debit V22: {v22:,.2f}"

        if st.button("💾 ARCHIVE DATA & FINISH DAY", use_container_width=True):
            entry = {
                "date": str(date.today()), "branch": branch, "staff": st.session_state['user'],
                "sales": sys_sales, "expenses": ex_val, "diff": diff, "kyo": ke-ks, "xerox": xe-xs
            }
            db["history"].append(entry)
            save_db(db); st.success("Day Archived Successfully!")

        col_rep1, col_rep2 = st.columns(2)
        with col_rep1:
            if st.button("📄 GENERATE DETAILED PDF", use_container_width=True):
                buf = io.BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
                styles = getSampleStyleSheet()
                parts = [Paragraph(f"NMS Enterprise - Full Shift Report - {branch}", styles['Title'])]
                p_data = [
                    ["Field", "Value"],
                    ["Staff", st.session_state['user']],
                    ["Sales", sys_sales],
                    ["Expenses", f"{ex_val} ({ex_note})"],
                    ["Drawer Cash", t_close],
                    ["Net Difference", diff],
                    ["Kyo Total", ke-ks],
                    ["Xerox Total", xe-xs]
                ]
                tbl = Table(p_data, colWidths=[200, 300])
                tbl.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.grey)]))
                parts.append(tbl); doc.build(parts)
                st.download_button("📥 Download PDF", buf.getvalue(), f"NMS_{branch}_{date.today()}.pdf")
        
        with col_rep2:
            wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 WHATSAPP FULL REPORT</button></a>', unsafe_allow_html=True)
