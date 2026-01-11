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

# ==========================================
# 1. DATABASE & CONFIGURATION
# ==========================================
DB_FILE = 'nms_enterprise_db.json'
MANAGER_PHONE = "971522045638"

def load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return {
            "logo": None,
            "pending_debit": 0.0,
            "users": {
                "admin": {"pass": "admin123", "role": "admin", "full_name": "Manager"},
                "Mina": {"pass": "123", "role": "user", "full_name": "Mina"}
            },
            "branches": ["M. Nageb Branch", "Tram Branch"],
            "tasks": {
                "opening": ["Fingerprint", "Power On", "Uniform", "Cash Counted"],
                "closing": ["Place Cleaned", "Power Off", "Cash Counted", "Report Sent"],
                "social": ["WhatsApp Story", "Facebook Post", "Instagram Story", "TikTok Post"],
                "interaction": ["Like", "Share", "Comment"]
            },
            "logs": [], "drafts": {}, "history": []
        }
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        if "history" not in data: data["history"] = []
        return data

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4) # indent=4 بيخلي ملف الـ JSON مقروء ومرتب

db = load_db()

# ==========================================
# 2. SESSION & AUTO-SAVE LOGIC
# ==========================================
st.set_page_config(page_title="NMS ERP v2.0", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        # حفظ كل المدخلات اللي بتبدأ برموز معينة لضمان عدم ضياع البيانات
        current_data = {k: v for k, v in st.session_state.items() if k.startswith(('s_', 'o_', 'm_', 'e_', 'c_', 'i_', 'ks', 'xs', 'ops', 'oc', 'cc', 'k1', 'x2', 'u10_', 'v22_'))}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = current_data
        save_db(db)

# ==========================================
# 3. LOGIN INTERFACE
# ==========================================
if not st.session_state['logged_in']:
    st.title("🚀 NMS Enterprise - Login")
    col1, col2 = st.columns([1, 1])
    with col2:
        u = st.selectbox("Select Employee", list(db["users"].keys()))
        p = st.text_input("Password", type="password")
        if st.button("Access System", use_container_width=True):
            if db["users"][u]["pass"] == p:
                st.session_state.update({'logged_in': True, 'user': u, 'role': db["users"][u].get("role", "user")})
                # استرجاع المسودة (Draft) إذا وجدت
                if u in db.get("drafts", {}):
                    for key, val in db["drafts"][u].items():
                        st.session_state[key] = val
                db["logs"].append({"user": u, "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "action": "Login"})
                save_db(db)
                st.rerun()
            else:
                st.error("Authentication Failed")
else:
    # ==========================================
    # 4. SIDEBAR & ADMIN CONTROLS
    # ==========================================
    with st.sidebar:
        st.header(f"👤 {st.session_state['user']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

        # لوحة تحكم المدير - تظهر فقط للأدمن
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("⚙️ Admin Dashboard")
            adm_choice = st.radio("Management", ["Employees", "History Review", "App Settings"])
            
            if adm_choice == "Employees":
                target = st.selectbox("Select User", list(db["users"].keys()))
                new_p = st.text_input("Change Password", db["users"][target]["pass"])
                new_r = st.selectbox("Role", ["admin", "user"], index=0 if db["users"][target]["role"]=="admin" else 1)
                if st.button("Save Changes"):
                    db["users"][target]["pass"] = new_p
                    db["users"][target]["role"] = new_r
                    save_db(db); st.success("Updated!")

    # ==========================================
    # 5. MAIN DASHBOARD
    # ==========================================
    st.title("📊 Daily Shift Management")
    inf1, inf2, inf3, inf4 = st.columns(4)
    with inf3: branch = st.selectbox("Branch", db["branches"])
    with inf4: shift = st.selectbox("Shift", ["Morning", "Night"])

    tab1, tab2, tab3 = st.tabs(["🟢 Opening", "🔴 Closing", "📱 Social Media"])

    # --- TAB 1: OPENING ---
    with tab1:
        if db.get("pending_debit", 0) > 0:
            st.warning(f"⚠️ Pending Debit: {db['pending_debit']:,.2f}")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Checklist**")
            for t in db["tasks"]["opening"]: st.checkbox(t, key=f"s_{t}", on_change=sync_draft)
        with c2:
            st.write("**Opening Cash**")
            t_open = sum([st.number_input(f"{d} LE", 0, key=f"o_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
            t_open += st.number_input("Coins", 0.0, key="oc", on_change=sync_draft)
            st.success(f"Total: {t_open:,.2f}")
        with c3:
            st.write("**Start Counters**")
            ks = st.number_input("Kyocera Start", 0, key="ks", on_change=sync_draft)
            xs = st.number_input("Xerox Start", 0, key="xs", on_change=sync_draft)
            u10 = st.number_input("Debit Received", 0.0, key="u10_val", on_change=sync_draft)

    # --- TAB 2: CLOSING (التركيز هنا) ---
    with tab2:
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.write("**Financial Input**")
            sys_sales = st.number_input("System Sales", 0.0, key="c_sys_sales", on_change=sync_draft)
            v22 = st.number_input("Debit Out", 0.0, key="v22_val", on_change=sync_draft)
            e_pay = st.number_input("Instapay", 0.0, key="c_insta") + st.number_input("Wallet", 0.0, key="c_wall") + st.number_input("Visa", 0.0, key="c_visa")
            exp = st.number_input("Expenses", 0.0, key="c_exp", on_change=sync_draft)
        with c2:
            st.write("**Closing Cash**")
            t_close = sum([st.number_input(f"{d} LE ", 0, key=f"c_{d}", on_change=sync_draft)*d for d in [200, 100, 50, 20, 10, 5]])
            t_close += st.number_input("Closing Coins", 0.0, key="cc", on_change=sync_draft)
            st.divider()
            
            # حساب الحالة المالية - تظهر للجميع
            expected = t_open + sys_sales + u10 - exp - v22 - e_pay
            net_diff = t_close - expected
            st.metric("Expected in Drawer", f"{expected:,.2f}", delta=f"{net_diff:,.2f}")
            if abs(net_diff) < 1: st.success("✅ Match")
            else: st.error(f"❌ Diff: {net_diff:,.2f}")

        with c3:
            st.write("**Printer Analysis**")
            # زيروكس كاملة
            st.markdown("--- Xerox ---")
            xe = st.number_input("Xerox End", 0, key="x2end")
            x_acc = st.number_input("X-OS", 0, key="x2os") + (st.number_input("X-DP", 0, key="x2dp")*2) + st.number_input("X-Jam", 0, key="x2err") + st.number_input("X-Test", 0, key="x2tst")
            x_real = xe - xs
            if (x_acc - x_real) == 0: st.success(f"Xerox OK ({x_real})")
            else: st.warning(f"Xerox Diff: {x_acc - x_real}")

    # --- TAB 3: SOCIAL ---
    with tab3:
        cols = st.columns(4)
        for i, t in enumerate(db["tasks"]["social"]):
            cols[i%4].checkbox(t, key=f"m_{t}", on_change=sync_draft)

    # ==========================================
    # 6. SUBMISSION & WHATSAPP
    # ==========================================
    if st.button("🏁 FINALIZE SHIFT", use_container_width=True):
        # كود الأرشفة
        arc = {"date": str(datetime.now().date()), "staff": st.session_state['user'], "branch": branch, "net_diff": net_diff}
        db["history"].append(arc)
        db["pending_debit"] = v22
        save_db(db)
        st.balloons()
        st.success("Shift Archived!")
