# app.py
import streamlit as st
from datetime import datetime, date
import base64

# خدمات المشروع المفصّلة في الملفات المنفصلة
from database_service import load_db, save_db, get_manager_phone
from operations_service import daily_operations_ui
from printer_service import init_printers

# تأكد من تهيئة الطابعات الافتراضية (يمرر init_printers() مرة واحدة)
init_printers()

# تكوين الصفحة
st.set_page_config(page_title="NMS ERP", layout="wide", page_icon="📊")

# تحميل قاعدة البيانات
db = load_db()

# SESSION STATE defaults
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "user": None, "role": None})

# ---------- Login screen ----------
if not st.session_state.get("logged_in"):
    st.title("🔐 NMS Enterprise Login")

    c1, c2 = st.columns([1, 2])
    with c1:
        if db.get("logo"):
            try:
                st.image(base64.b64decode(db["logo"]), width=260)
            except:
                st.info("Company logo present but failed to render.")
        else:
            st.info("Upload company logo in Admin panel.")

    with c2:
        st.write("### Login")
        users = list(db.get("users", {}).keys())
        if not users:
            st.error("No users in DB. Please init database or add users.")
            st.stop()

        username = st.selectbox("Select account", users)
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            user_rec = db["users"].get(username, {})
            if user_rec and user_rec.get("pass") == password:
                st.session_state.update({
                    "logged_in": True,
                    "user": username,
                    "role": user_rec.get("role", "user")
                })
                # restore draft if present
                if username in db.get("drafts", {}):
                    for k, v in db["drafts"][username].items():
                        st.session_state[k] = v
                # log
                db.setdefault("logs", []).append({
                    "user": username,
                    "time": datetime.now().isoformat(),
                    "action": "login"
                })
                save_db(db)
                st.experimental_rerun()
            else:
                st.error("Incorrect credentials")

    st.stop()

# ---------- After login: Sidebar & Main ----------
with st.sidebar:
    user_info = db.get("users", {}).get(st.session_state.get("user"), {})
    st.header(f"Hello, {user_info.get('full_name', st.session_state.get('user'))}")
    if user_info.get("photo"):
        try:
            st.image(base64.b64decode(user_info["photo"]), width=110)
        except:
            pass

    st.markdown("---")
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.experimental_rerun()

    st.markdown("### Quick")
    st.write(f"Role: **{st.session_state.get('role')}**")
    st.write(f"Branch: {db.get('branches', ['-'])[0] if db.get('branches') else '-'}")
    st.markdown("---")
    if st.session_state.get("role") == "admin":
        st.markdown("⚙️ Admin: Use menu in main UI (or open Admin page)")

# ---------- Main: call daily operations UI ----------
daily_operations_ui(db)
