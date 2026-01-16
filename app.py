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

# --- 1. Database Engine & Setup ---
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
        # Ensure new HR fields exist for all users
        for user in data["users"]:
            if "bonus" not in data["users"][user]: data["users"][user]["bonus"] = []
            if "deductions" not in data["users"][user]: data["users"][user]["deductions"] = []
            if "salary" not in data["users"][user]: data["users"][user]["salary"] = 0.0
            if "hiring_date" not in data["users"][user]: data["users"][user]["hiring_date"] = "2024-01-01"
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

db = load_db()

# --- 2. Styling & State Management ---
st.set_page_config(page_title="NMS ERP - Enterprise", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # Save all relevant session keys to draft
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'op_', 'u10_', 'v22_', 'exp_'))}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# --- 3. Authentication ---
if not st.session_state['logged_in']:
    st.title("🚀 NMS ERP - Enterprise Login")
    col1, col2 = st.columns([1, 1])
    with col1:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=250)
    with col2:
        u = st.selectbox("Select Employee", list(db["users"].keys()))
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u]["role"]})
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items(): st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "action": "Login"})
                save_db(db); st.rerun()
            else: st.error("Wrong Password")
else:
    # --- 4. Sidebar & Admin Panel ---
    with st.sidebar:
        if db.get("logo"): st.image(base64.b64decode(db["logo"]), width=120)
        st.header(f"Hi, {db['users'][st.session_state['user']]['full_name']}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()

        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("🛠️ Admin Master Control")
            admin_mode = st.radio("Menu", ["HR & Payroll", "Manage Tasks", "Manage Branches", "Manage Expenses", "History & Archives", "Audit Logs"])

            # 4.1 HR & PAYROLL
            if admin_mode == "HR & Payroll":
                st.subheader("Employee Financials")
                target = st.selectbox("Select Employee", list(db["users"].keys()))
                emp = db["users"][target]
                
                tab_sal, tab_bd = st.tabs(["Salary Settings", "Bonus & Deductions"])
                with tab_sal:
                    new_sal = st.number_input("Monthly Salary", value=float(emp.get('salary', 0)))
                    new_hire = st.date_input("Hiring Date", value=datetime.strptime(emp.get('hiring_date', "2024-01-01"), "%Y-%m-%d"))
                    if st.button("Update Contract"):
                        db["users"][target].update({"salary": new_sal, "hiring_date": str(new_hire)})
                        save_db(db); st.success("Updated")
                with tab_bd:
                    c1, c2 = st.columns(2)
                    amt = st.number_input("Amount", step=50.0)
                    reason = st.text_input("Note")
                    if c1.button("Grant Bonus"):
                        db["users"][target]["bonus"].append({"date": str(date.today()), "amt": amt, "reason": reason})
                        save_db(db); st.success("Bonus Added")
                    if c2.button("Apply Deduction"):
                        db["users"][target]["deductions"].append({"date": str(date.today()), "amt": amt, "reason": reason})
                        save_db(db); st.warning("Deduction Added")

            # 4.2 MANAGE TASKS (Restored)
            elif admin_mode == "Manage Tasks":
                st.subheader("Task Lists Editor")
                cat = st.selectbox("Category", ["opening", "closing", "social", "interaction"])
                for i, t in enumerate(db["tasks"][cat]):
                    col_t1, col_t2 = st.columns([4, 1])
                    col_t1.text(f"• {t}")
                    if col_t2.button("🗑️", key=f"dt_{cat}_{i}"):
                        db["tasks"][cat].pop(i); save_db(db); st.rerun()
                new_t = st.text_input("Add Task")
                if st.button("Add"):
                    if new_t: db["tasks"][cat].append(new_t); save_db(db); st.rerun()

            # 4.3 MANAGE BRANCHES
            elif admin_mode == "Manage Branches":
                st.subheader("Branches List")
                for i, b in enumerate(db["branches"]):
                    col_b1, col_b2 = st.columns([4, 1])
                    col_b1.text(b)
                    if col_b2.button("🗑️", key=f"db_{i}"):
                        db["branches"].pop(i); save_db(db); st.rerun()
                new_b = st.text_input("New Branch")
                if st.button("Add Branch"):
                    if new_b: db["branches"].append(new_b); save_db(db); st.rerun()

            # 4.4 MANAGE EXPENSES
            elif admin_mode == "Manage Expenses":
                st.subheader("Expense Categories")
                for i, e in enumerate(db["expense_categories"]):
                    col_e1, col_e2 = st.columns([4, 1])
                    col_e1.text(e)
                    if col_e2.button("🗑️", key=f"de_{i}"):
                        db["expense_categories"].pop(i); save_db(db); st.rerun()
                new_e = st.text_input("New Category")
                if st.button("Add Category"):
                    if new_e: db["expense_categories"].append(new_e); save_db(db); st.rerun()

            # 4.5 HISTORY & ARCHIVES
            elif admin_mode == "History & Archives":
                st.subheader("Shift History")
                if db["history"]:
                    st.dataframe(pd.DataFrame(db["history"]))
                    if st.button("Clear History (Permanent)", type="primary"):
                        db["history"] = []; save_db(db); st.rerun()
                else: st.info("History Empty")

    # --- 5. Main Content (The Shift Form) ---
    st.title("📊 Daily Shift Report")
    m1, m2, m3, m4 = st.columns(4)
    with m1: branch = st.selectbox("Branch", db["branches"])
    with m2: shift = st.selectbox("Shift", ["Morning", "Night"])
    with m3: st.info(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    with m4: st.info(f"👤 {st.session_state['user']}")

    tab_open, tab_close, tab_social = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL & INTERACTION"])

    # --- OPENING TAB ---
    with tab_open:
        st.subheader("Opening Procedures")
        col_o1, col_o2, col_o3 = st.columns([1, 1.5, 1.5])
        with col_o1:
            st.write("**Checklist**")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with col_o2:
            st.write("**Opening Cash (Drawer)**")
            t_open = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                count = st.number_input(f"{d} LE", min_value=0, step=1, key=f"o_{d}", on_change=sync_draft)
                t_open += (count * d)
            o_coins = st.number_input("Coins", step=0.5, key="oc", on_change=sync_draft)
            t_open += o_coins
            st.success(f"**Total Opening: {t_open:,.2f}**")
        with col_o3:
            st.write("**Starting Counters**")
            k_start = st.number_input("Kyocera Start", step=1, key="ks", on_change=sync_draft)
            x_start = st.number_input("Xerox Start", step=1, key="xs", on_change=sync_draft)
            ops = st.number_input("Opay Start", step=0.01, key="ops", on_change=sync_draft)
            u10 = st.number_input("Debit In (U10)", step=1.0, key="u10_val", on_change=sync_draft)

    # --- CLOSING TAB ---
    with tab_close:
        st.subheader("Closing Procedures")
        col_c1, col_c2, col_c3 = st.columns([1, 1.5, 1.5])
        with col_c1:
            st.write("**Closing Checklist**")
            for t in db["tasks"]["closing"]: st.checkbox(t, key=f"e_{t}", on_change=sync_draft)
            st.divider()
            sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales", on_change=sync_draft)
            v22_debit = st.number_input("Debit Out (V22)", step=1.0, key="v22_val", on_change=sync_draft)
            instapay = st.number_input("Instapay", step=1.0, key="c_insta", on_change=sync_draft)
            wallet = st.number_input("Wallet/Vodafone", step=1.0, key="c_wall", on_change=sync_draft)
            visa = st.number_input("Visa/Credit", step=1.0, key="c_visa", on_change=sync_draft)
            t_e_pay = instapay + wallet + visa
        with col_c2:
            st.write("**Closing Cash (Actual)**")
            t_close = 0.0
            for d in [200, 100, 50, 20, 10, 5]:
                count = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"c_{d}", on_change=sync_draft)
                t_close += (count * d)
            c_coins = st.number_input("Coins ", step=0.5, key="cc", on_change=sync_draft)
            t_close += c_coins
            st.divider()
            st.write("**Daily Expenses**")
            ex_cat = st.selectbox("Category", db["expense_categories"], key="exp_cat_sel")
            ex_val = st.number_input("Expense Amount", step=1.0, key="c_exp")
            ex_note = st.text_input("Expense Reason")
            
            # --- FINANCIAL CALCULATION ---
            expected = t_open + sys_sales + u10 - ex_val - v22_debit - t_e_pay
            net_diff = t_close - expected
            st.metric("Expected Cash", f"{expected:,.2f}")
            if abs(net_diff) < 0.1: st.success("Matched!")
            else: st.error(f"Difference: {net_diff:,.2f}")
        with col_c3:
            st.write("**Ending Counters**")
            k_end = st.number_input("Kyocera End", step=1, key="k1end", on_change=sync_draft)
            x_end = st.number_input("Xerox End", step=1, key="x2end", on_change=sync_draft)
            op_end = st.number_input("Opay End", step=0.01, key="op_end", on_change=sync_draft)
            st.write(f"K Used: {k_end - k_start}")
            st.write(f"X Used: {x_end - x_start}")
            st.write(f"Opay Change: {ops - op_end:,.2f}")

    # --- SOCIAL TAB ---
    with tab_social:
        st.subheader("Social Media Tasks")
        s1, s2 = st.columns(2)
        with s1:
            for t in db["tasks"]["social"]: st.checkbox(t, key=f"m_{t}", on_change=sync_draft)
        with s2:
            for t in db["tasks"]["interaction"]: st.checkbox(t, key=f"i_{t}", on_change=sync_draft)

    # --- 6. Final Submission & WhatsApp ---
    st.divider()
    if st.button("🏁 FINISH & ARCHIVE SHIFT", use_container_width=True):
        archive = {
            "date": str(date.today()),
            "branch": branch,
            "staff": st.session_state['user'],
            "sales": sys_sales,
            "expenses": ex_val,
            "exp_note": f"{ex_cat}: {ex_note}",
            "net_diff": net_diff,
            "kyo": k_end - k_start,
            "xerox": x_end - x_start
        }
        db["history"].append(archive)
        save_db(db); st.success("Shift Successfully Archived")

    # WhatsApp Report Generation
    rep_text = f"*🚀 NMS ERP REPORT*\n*Date:* {date.today()}\n*Staff:* {st.session_state['user']}\n*Branch:* {branch}\n\n*💰 Finance:*\n- Sales: {sys_sales:,.2f}\n- Exp: {ex_val:,.2f} ({ex_cat})\n- Drawer: {t_close:,.2f}\n- Diff: {net_diff:,.2f}\n\n*🖨️ Counters:*\n- Kyo: {k_end-k_start}\n- Xerox: {x_end-x_start}"
    wa_url = f"https://wa.me/{MANAGER_PHONE}?text={urllib.parse.quote(rep_text)}"
    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; font-weight:bold;">📱 SEND WHATSAPP REPORT</button></a>', unsafe_allow_html=True)
