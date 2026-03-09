# =====================================================
# AUTH SERVICE
# =====================================================

from datetime import datetime

import streamlit as st


# =====================================================
# Helpers
# =====================================================
def get_user_record(db: dict, username: str) -> dict:
    return db.get("users", {}).get(username, {})


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in", False))


def get_current_username() -> str | None:
    return st.session_state.get("user")


def get_current_role() -> str | None:
    return st.session_state.get("role")


def is_admin() -> bool:
    return get_current_role() == "admin"


def require_login() -> bool:
    return is_logged_in() and bool(get_current_username())


def require_admin() -> bool:
    return require_login() and is_admin()


def log_auth_event(db: dict, username: str, action: str) -> None:
    """
    Temporary safe logger:
    keep auth logs in memory only, without saving the whole database.

    Reason:
    current project moved to Supabase, while logs are not yet migrated
    and save_db(db) performs a full sync that can break login/logout.
    """
    try:
        db.setdefault("logs", []).append(
            {
                "user": username,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": action,
            }
        )
    except Exception:
        pass


# =====================================================
# Draft helpers
# =====================================================
def get_draft_prefixes() -> tuple[str, ...]:
    return (
        "s_",
        "o_",
        "e_",
        "c_",
        "m_",
        "i_",
        "ks",
        "xs",
        "op",
        "u10",
        "v22",
        "ex",
        "kj",
        "xj",
        "dn",
        "k1",
        "k2",
        "x1",
        "x2",
    )


def sync_user_drafts(db: dict) -> None:
    """
    Temporary safe draft sync:
    store drafts in runtime memory only, without calling save_db(db).
    """
    if not is_logged_in():
        return

    username = get_current_username()
    if not username:
        return

    prefixes = get_draft_prefixes()

    draft_data = {
        key: value
        for key, value in st.session_state.items()
        if key.startswith(prefixes)
    }

    db.setdefault("drafts", {})
    db["drafts"][username] = draft_data


def restore_user_drafts(db: dict, username: str) -> None:
    drafts = db.get("drafts", {}).get(username, {})
    for key, value in drafts.items():
        st.session_state[key] = value


def clear_user_session() -> None:
    keep_keys = {"theme"}
    keys_to_remove = [key for key in st.session_state.keys() if key not in keep_keys]

    for key in keys_to_remove:
        del st.session_state[key]


# =====================================================
# Password helpers
# =====================================================
def verify_password(user_record: dict, password: str) -> bool:
    """
    Current project still uses plain-text passwords.
    This helper isolates verification so we can later switch
    to hashed passwords without changing the whole app.
    """
    stored_password = user_record.get("pass", "")
    return stored_password == password


# =====================================================
# Login / Logout
# =====================================================
def login_user(db: dict, username: str, password: str) -> tuple[bool, str]:
    users = db.get("users", {})

    if username not in users:
        return False, "User not found."

    user_record = users[username]

    if not verify_password(user_record, password):
        return False, "Invalid password."

    st.session_state["logged_in"] = True
    st.session_state["user"] = username
    st.session_state["role"] = user_record.get("role", "user")

    restore_user_drafts(db, username)
    log_auth_event(db, username, "Login")

    return True, "Login successful."


def logout_user(db: dict) -> None:
    username = get_current_username() or "unknown"

    sync_user_drafts(db)
    log_auth_event(db, username, "Logout")

    clear_user_session()


# =====================================================
# UI
# =====================================================
def render_login_screen(db: dict) -> None:
    st.title("🔐 NMS Enterprise Access")

    users = list(db.get("users", {}).keys())
    if not users:
        st.error("No users found in database. Please create an admin user first.")
        st.stop()

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        st.write("### 🔑 Secure Login")

        username = st.selectbox("Select Your Account", users)
        password = st.text_input("Enter Password", type="password")

        if st.button("🚀 Login", use_container_width=True):
            success, message = login_user(db, username, password)

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(f"❌ {message}")

    st.stop()
