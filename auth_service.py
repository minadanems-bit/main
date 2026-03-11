# =====================================================
# AUTH SERVICE
# =====================================================

from datetime import datetime

import streamlit as st


# =====================================================
# Shift rules
# =====================================================
SHIFT_START_RULES = {
    "Morning": {"hour": 8, "minute": 0},
    "Between": {"hour": 12, "minute": 0},
    "Night": {"hour": 15, "minute": 0},
}

LATE_GRACE_MINUTES = 5
MAX_LATE_BEFORE_BLOCK = 4


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


def get_current_month_key() -> str:
    return datetime.now().strftime("%Y-%m")


def get_shift_start_total_minutes(shift_name: str) -> int:
    shift_data = SHIFT_START_RULES.get(shift_name, SHIFT_START_RULES["Morning"])
    return (shift_data["hour"] * 60) + shift_data["minute"]


def get_arrival_total_minutes(hour_value: int, minute_value: int) -> int:
    return (int(hour_value) * 60) + int(minute_value)


def calculate_late_minutes(shift_name: str, arrival_hour: int, arrival_minute: int) -> int:
    shift_start = get_shift_start_total_minutes(shift_name)
    allowed_latest = shift_start + LATE_GRACE_MINUTES
    arrival_total = get_arrival_total_minutes(arrival_hour, arrival_minute)
    return max(0, arrival_total - allowed_latest)


def ensure_attendance_defaults(db: dict) -> None:
    db.setdefault("attendance_records", {})
    db.setdefault("late_tracking", {})
    db.setdefault("blocked_users", {})


def get_user_month_late_count(db: dict, username: str) -> int:
    ensure_attendance_defaults(db)
    month_key = get_current_month_key()
    return int(db.get("late_tracking", {}).get(month_key, {}).get(username, 0))


def set_user_month_late_count(db: dict, username: str, count: int) -> None:
    ensure_attendance_defaults(db)
    month_key = get_current_month_key()
    db["late_tracking"].setdefault(month_key, {})
    db["late_tracking"][month_key][username] = int(count)


def is_user_blocked_for_month(db: dict, username: str) -> bool:
    ensure_attendance_defaults(db)
    month_key = get_current_month_key()
    return bool(db.get("blocked_users", {}).get(month_key, {}).get(username, False))


def set_user_blocked_for_month(db: dict, username: str, blocked: bool) -> None:
    ensure_attendance_defaults(db)
    month_key = get_current_month_key()
    db["blocked_users"].setdefault(month_key, {})
    db["blocked_users"][month_key][username] = bool(blocked)


def append_attendance_record(
    db: dict,
    username: str,
    shift_name: str,
    arrival_hour: int,
    arrival_minute: int,
    late_minutes: int,
    status: str,
) -> None:
    ensure_attendance_defaults(db)
    month_key = get_current_month_key()
    db["attendance_records"].setdefault(month_key, {})
    db["attendance_records"][month_key].setdefault(username, [])
    db["attendance_records"][month_key][username].append(
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": f"{int(arrival_hour):02d}:{int(arrival_minute):02d}",
            "shift": shift_name,
            "late_minutes": int(late_minutes),
            "status": status,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def get_late_warning_message(late_count: int, late_minutes: int) -> str:
    if late_count <= 1:
        return (
            f"⚠️ أنت متأخر اليوم بمقدار {late_minutes} دقيقة بعد فترة السماح.\n\n"
            f"التأخير أكثر من 3 مرات خلال نفس الشهر يساوي خصم يوم من الراتب."
        )

    if late_count == 2:
        return (
            f"⚠️ هذا هو التأخير رقم 2 خلال هذا الشهر.\n\n"
            f"أنت متأخر اليوم بمقدار {late_minutes} دقيقة.\n"
            f"يجب الاحتراس حتى لا يتم تطبيق الخصم."
        )

    if late_count == 3:
        return (
            f"⚠️ هذا هو التأخير رقم 3 خلال هذا الشهر.\n\n"
            f"أنت متأخر اليوم بمقدار {late_minutes} دقيقة.\n"
            f"سيتم احتساب خصم يوم من الراتب طبقًا للائحة."
        )

    return (
        f"⛔ هذا هو التأخير رقم {late_count} خلال هذا الشهر.\n\n"
        f"أنت متأخر اليوم بمقدار {late_minutes} دقيقة.\n"
        f"تم إيقاف دخول التشغيل اليومي لحين تصريح المدير."
    )


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
    stored_password = user_record.get("pass", "")
    return stored_password == password


# =====================================================
# Login / Logout
# =====================================================
def login_user(
    db: dict,
    username: str,
    password: str,
    shift_name: str,
    arrival_hour: int,
    arrival_minute: int,
    late_acknowledged: bool,
) -> tuple[bool, str]:
    users = db.get("users", {})

    if username not in users:
        return False, "User not found."

    user_record = users[username]

    if not verify_password(user_record, password):
        return False, "Invalid password."

    if is_user_blocked_for_month(db, username):
        st.session_state["login_blocked_message"] = (
            "⛔ تم إيقاف دخول التشغيل اليومي لهذا الموظف خلال هذا الشهر.\n"
            "يرجى مراجعة المدير للحصول على تصريح."
        )
        return False, "Daily operations access is blocked."

    late_minutes = calculate_late_minutes(shift_name, arrival_hour, arrival_minute)
    current_late_count = get_user_month_late_count(db, username)
    next_late_count = current_late_count + 1 if late_minutes > 0 else current_late_count

    if late_minutes > 0 and not late_acknowledged:
        warning_message = get_late_warning_message(next_late_count, late_minutes)
        st.session_state["pending_late_warning"] = warning_message
        st.session_state["pending_login_payload"] = {
            "username": username,
            "password": password,
            "shift_name": shift_name,
            "arrival_hour": int(arrival_hour),
            "arrival_minute": int(arrival_minute),
        }
        return False, "Late acknowledgement required."

    if late_minutes > 0:
        set_user_month_late_count(db, username, next_late_count)

        if next_late_count >= MAX_LATE_BEFORE_BLOCK:
            set_user_blocked_for_month(db, username, True)
            append_attendance_record(
                db=db,
                username=username,
                shift_name=shift_name,
                arrival_hour=arrival_hour,
                arrival_minute=arrival_minute,
                late_minutes=late_minutes,
                status="blocked_after_late",
            )
            st.session_state["login_blocked_message"] = get_late_warning_message(next_late_count, late_minutes)
            return False, "Daily operations access is blocked."

        append_attendance_record(
            db=db,
            username=username,
            shift_name=shift_name,
            arrival_hour=arrival_hour,
            arrival_minute=arrival_minute,
            late_minutes=late_minutes,
            status="late",
        )
    else:
        append_attendance_record(
            db=db,
            username=username,
            shift_name=shift_name,
            arrival_hour=arrival_hour,
            arrival_minute=arrival_minute,
            late_minutes=0,
            status="on_time",
        )

    st.session_state["logged_in"] = True
    st.session_state["user"] = username
    st.session_state["role"] = user_record.get("role", "user")
    st.session_state["attendance_shift"] = shift_name
    st.session_state["attendance_time"] = f"{int(arrival_hour):02d}:{int(arrival_minute):02d}"

    restore_user_drafts(db, username)
    log_auth_event(db, username, "Login")

    st.session_state.pop("pending_late_warning", None)
    st.session_state.pop("pending_login_payload", None)
    st.session_state.pop("login_blocked_message", None)

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

    blocked_message = st.session_state.get("login_blocked_message")
    if blocked_message:
        st.error(blocked_message)

    pending_warning = st.session_state.get("pending_late_warning")
    pending_payload = st.session_state.get("pending_login_payload")

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        st.write("### 🔑 Secure Login")

        username = st.selectbox("Select Your Account", users)
        password = st.text_input("Enter Password", type="password")

        st.write("### 🕒 Attendance Confirmation")
        shift_name = st.selectbox("Select Shift", list(SHIFT_START_RULES.keys()))

        h1, h2 = st.columns(2)
        with h1:
            arrival_hour = st.number_input(
                "Arrival Hour",
                min_value=0,
                max_value=23,
                value=8,
                step=1,
            )
        with h2:
            arrival_minute = st.number_input(
                "Arrival Minute",
                min_value=0,
                max_value=59,
                value=0,
                step=1,
            )

        if pending_warning and pending_payload:
            st.warning(pending_warning)
            late_acknowledged = st.checkbox(
                "I have read and accepted this warning.",
                key="late_warning_ack_checkbox",
            )

            if st.button("✅ Confirm And Continue", use_container_width=True):
                if not late_acknowledged:
                    st.error("You must acknowledge the warning first.")
                else:
                    success, message = login_user(
                        db=db,
                        username=pending_payload["username"],
                        password=pending_payload["password"],
                        shift_name=pending_payload["shift_name"],
                        arrival_hour=int(pending_payload["arrival_hour"]),
                        arrival_minute=int(pending_payload["arrival_minute"]),
                        late_acknowledged=True,
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        if message == "Daily operations access is blocked.":
                            st.error(st.session_state.get("login_blocked_message", message))
                        else:
                            st.error(f"❌ {message}")

        else:
            if st.button("🚀 Login", use_container_width=True):
                success, message = login_user(
                    db=db,
                    username=username,
                    password=password,
                    shift_name=shift_name,
                    arrival_hour=int(arrival_hour),
                    arrival_minute=int(arrival_minute),
                    late_acknowledged=False,
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    if message == "Late acknowledgement required.":
                        st.rerun()
                    elif message == "Daily operations access is blocked.":
                        st.error(st.session_state.get("login_blocked_message", message))
                    else:
                        st.error(f"❌ {message}")

    st.stop()
