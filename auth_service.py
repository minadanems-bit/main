# =====================================================
# AUTH SERVICE
# =====================================================

from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from constants import (
    MONTHLY_LATE_BLOCK_AT,
    ROLE_ADMIN,
    ROLE_CLEANER,
    ROLE_EMPLOYEE,
    ROLE_MANAGER,
    SESSION_BRANCH,
    SESSION_SHIFT,
    SHIFT_GRACE_MINUTES,
    SHIFT_START_TIMES,
)
from database import save_db


# =====================================================
# Session Keys
# =====================================================
SESSION_LOGGED_IN = "logged_in"
SESSION_USER = "user"
SESSION_ROLE = "role"

SESSION_PENDING_ATTENDANCE_USER = "pending_attendance_user"
SESSION_PENDING_ATTENDANCE_PASSWORD = "pending_attendance_password"
SESSION_PENDING_ATTENDANCE_ROLE = "pending_attendance_role"

SESSION_PENDING_LATE_WARNING = "pending_late_warning"
SESSION_PENDING_LOGIN_PAYLOAD = "pending_login_payload"
SESSION_LOGIN_BLOCKED_MESSAGE = "login_blocked_message"

SESSION_ATTENDANCE_TIME = "attendance_time"
SESSION_ATTENDANCE_SHIFT = "attendance_shift"


# =====================================================
# Helpers
# =====================================================
def get_user_record(db: dict, username: str) -> dict:
    return db.get("users", {}).get(username, {})


def is_logged_in() -> bool:
    return bool(st.session_state.get(SESSION_LOGGED_IN, False))


def get_current_username() -> str | None:
    return st.session_state.get(SESSION_USER)


def get_current_role() -> str | None:
    return st.session_state.get(SESSION_ROLE)


def is_admin() -> bool:
    return get_current_role() == ROLE_ADMIN


def require_login() -> bool:
    return is_logged_in() and bool(get_current_username())


def require_admin() -> bool:
    return require_login() and is_admin()


def log_auth_event(db: dict, username: str, action: str) -> None:
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
    shift_data = SHIFT_START_TIMES.get(shift_name, SHIFT_START_TIMES["Morning"])
    return (int(shift_data["hour"]) * 60) + int(shift_data["minute"])


def get_arrival_total_minutes(hour_value: int, minute_value: int) -> int:
    return (int(hour_value) * 60) + int(minute_value)


def calculate_late_minutes(shift_name: str, arrival_hour: int, arrival_minute: int) -> int:
    shift_start = get_shift_start_total_minutes(shift_name)
    allowed_latest = shift_start + int(SHIFT_GRACE_MINUTES)
    arrival_total = get_arrival_total_minutes(arrival_hour, arrival_minute)
    return max(0, arrival_total - allowed_latest)


def ensure_attendance_defaults(db: dict) -> None:
    db.setdefault("attendance_records", {})
    db.setdefault("late_tracking", {})
    db.setdefault("blocked_users", {})
    db.setdefault("users", {})


def is_management_user(user_record: dict) -> bool:
    role_value = str(user_record.get("role", "") or "").strip().lower()
    return role_value in [ROLE_ADMIN, ROLE_MANAGER]


def requires_post_login_attendance_step(user_record: dict) -> bool:
    role_value = str(user_record.get("role", "") or "").strip().lower()
    return role_value in [ROLE_EMPLOYEE, ROLE_CLEANER]


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
    branch_name: str = "",
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
            "branch": branch_name,
            "late_minutes": int(late_minutes),
            "status": status,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def add_user_warning(db: dict, username: str, note: str) -> None:
    db.setdefault("users", {})
    user_record = db["users"].get(username, {})
    user_record.setdefault("warnings", [])
    user_record["warnings"].append(
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "note": note,
        }
    )


def has_late_penalty_this_month(user_record: dict, month_key: str) -> bool:
    penalties = user_record.get("late_penalties", [])
    for item in penalties:
        item_date = str(item.get("date", "") or "")
        if item_date.startswith(month_key):
            note = str(item.get("note", "") or "").lower()
            if "late" in note or "تأخير" in note:
                return True
    return False


def add_monthly_late_penalty_if_needed(db: dict, username: str) -> None:
    db.setdefault("users", {})
    user_record = db["users"].get(username, {})
    user_record.setdefault("late_penalties", [])

    month_key = get_current_month_key()
    if has_late_penalty_this_month(user_record, month_key):
        return

    monthly_salary = float(user_record.get("salary", 0) or 0)
    penalty_amount = round(monthly_salary / 30, 2) if monthly_salary > 0 else 0.0

    user_record["late_penalties"].append(
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "amount": penalty_amount,
            "note": "خصم يوم بسبب 3 مرات تأخير خلال نفس الشهر",
        }
    )


def persist_auth_changes(db: dict) -> None:
    try:
        save_db(db)
    except Exception:
        pass


def get_late_warning_message(late_count: int, late_minutes: int) -> str:
    if late_count == 1:
        return (
            f"⚠️ أنت متأخر اليوم بمقدار {late_minutes} دقيقة بعد فترة السماح.\n\n"
            "التأخير أكثر من 3 مرات خلال نفس الشهر يساوي خصم يوم من الراتب."
        )

    if late_count == 2:
        return (
            f"⚠️ هذا هو التأخير رقم 2 خلال هذا الشهر.\n\n"
            f"أنت متأخر اليوم بمقدار {late_minutes} دقيقة.\n"
            "يجب الاحتراس حتى لا يتم تطبيق الخصم."
        )

    if late_count == 3:
        return (
            f"⚠️ هذا هو التأخير رقم 3 خلال هذا الشهر.\n\n"
            f"أنت متأخر اليوم بمقدار {late_minutes} دقيقة.\n"
            "سيتم احتساب خصم يوم من الراتب طبقًا للائحة."
        )

    return (
        f"⛔ هذا هو التأخير رقم {late_count} خلال هذا الشهر.\n\n"
        f"أنت متأخر اليوم بمقدار {late_minutes} دقيقة.\n"
        "تم إيقاف دخول التشغيل اليومي لحين تصريح المدير."
    )


def clear_pending_login_flow() -> None:
    st.session_state.pop(SESSION_PENDING_ATTENDANCE_USER, None)
    st.session_state.pop(SESSION_PENDING_ATTENDANCE_PASSWORD, None)
    st.session_state.pop(SESSION_PENDING_ATTENDANCE_ROLE, None)
    st.session_state.pop(SESSION_PENDING_LATE_WARNING, None)
    st.session_state.pop(SESSION_PENDING_LOGIN_PAYLOAD, None)
    st.session_state.pop(SESSION_LOGIN_BLOCKED_MESSAGE, None)


def render_attendance_clock_widget(height: int = 300) -> None:
    components.html(
        """
        <div style="
            margin: 8px 0 18px 0;
            padding: 22px;
            border-radius: 22px;
            background: linear-gradient(135deg, #020617, #0f172a, #1e293b);
            color: white;
            box-shadow: 0 14px 32px rgba(0,0,0,0.22);
            border: 1px solid rgba(255,255,255,0.08);
        ">
            <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:28px;">
                <div style="min-width:260px;">
                    <div style="font-size:14px; opacity:0.8; margin-bottom:10px; letter-spacing:0.5px;">
                        ⏰ Current Attendance Time
                    </div>

                    <div id="digital-clock-login"
                         style="font-size:42px; font-weight:800; letter-spacing:2px; line-height:1;">
                        --:--:--
                    </div>

                    <div id="digital-ampm-login"
                         style="font-size:18px; font-weight:700; color:#38bdf8; margin-top:8px;">
                        --
                    </div>

                    <div id="digital-date-login"
                         style="font-size:14px; opacity:0.82; margin-top:10px;">
                        --
                    </div>
                </div>

                <div style="display:flex; justify-content:center; align-items:center; min-width:190px;">
                    <div id="analog-clock-login"
                         style="
                            position:relative;
                            width:165px;
                            height:165px;
                            border:6px solid rgba(255,255,255,0.88);
                            border-radius:50%;
                            background: radial-gradient(circle, #1e293b 55%, #0f172a 100%);
                            box-shadow: inset 0 0 20px rgba(255,255,255,0.06);
                         ">

                        <div style="position:absolute; top:50%; left:50%; width:12px; height:12px; background:#ffffff; border-radius:50%; transform:translate(-50%,-50%); z-index:10;"></div>

                        <div style="position:absolute; top:12px; left:76px; color:white; font-size:13px;">12</div>
                        <div style="position:absolute; top:72px; right:12px; color:white; font-size:13px;">3</div>
                        <div style="position:absolute; bottom:10px; left:78px; color:white; font-size:13px;">6</div>
                        <div style="position:absolute; top:72px; left:12px; color:white; font-size:13px;">9</div>

                        <div id="hour-hand-login"
                             style="position:absolute; width:5px; height:46px; background:#ffffff; top:36px; left:77px; transform-origin:bottom center; border-radius:4px;"></div>

                        <div id="minute-hand-login"
                             style="position:absolute; width:3px; height:62px; background:#cbd5e1; top:20px; left:78px; transform-origin:bottom center; border-radius:4px;"></div>

                        <div id="second-hand-login"
                             style="position:absolute; width:2px; height:70px; background:#38bdf8; top:12px; left:78.5px; transform-origin:bottom center; border-radius:4px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function updateClockLogin() {
                const now = new Date();

                const hh24 = now.getHours();
                const mm = String(now.getMinutes()).padStart(2, '0');
                const ss = String(now.getSeconds()).padStart(2, '0');

                const ampm = hh24 >= 12 ? 'PM' : 'AM';
                let hh12 = hh24 % 12;
                if (hh12 === 0) hh12 = 12;
                const hh12Text = String(hh12).padStart(2, '0');

                const dateText = now.toLocaleDateString(undefined, {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });

                const digital = document.getElementById("digital-clock-login");
                const ampmEl = document.getElementById("digital-ampm-login");
                const dateEl = document.getElementById("digital-date-login");
                const hourHand = document.getElementById("hour-hand-login");
                const minuteHand = document.getElementById("minute-hand-login");
                const secondHand = document.getElementById("second-hand-login");

                if (!digital || !ampmEl || !dateEl || !hourHand || !minuteHand || !secondHand) return;

                digital.innerText = `${hh12Text}:${mm}:${ss}`;
                ampmEl.innerText = ampm;
                dateEl.innerText = dateText;

                const seconds = now.getSeconds();
                const minutes = now.getMinutes();
                const hours = now.getHours();

                const secondDeg = seconds * 6;
                const minuteDeg = (minutes * 6) + (seconds * 0.1);
                const hourDeg = ((hours % 12) * 30) + (minutes * 0.5);

                secondHand.style.transform = `rotate(${secondDeg}deg)`;
                minuteHand.style.transform = `rotate(${minuteDeg}deg)`;
                hourHand.style.transform = `rotate(${hourDeg}deg)`;
            }

            updateClockLogin();
            setInterval(updateClockLogin, 1000);
        </script>
        """,
        height=height,
    )


def render_professional_time_picker(
    title: str,
    default_hour_24: int,
    default_minute: int,
    key_prefix: str,
) -> tuple[int, int]:
    st.markdown(f"### {title}")

    hour_options_12 = list(range(1, 13))
    minute_options = list(range(0, 60, 5))

    default_ampm = "AM" if default_hour_24 < 12 else "PM"
    default_hour_12 = default_hour_24 % 12
    if default_hour_12 == 0:
        default_hour_12 = 12

    if default_minute not in minute_options:
        closest_minute = min(minute_options, key=lambda x: abs(x - default_minute))
    else:
        closest_minute = default_minute

    c1, c2, c3 = st.columns([1.2, 1.2, 1])

    with c1:
        selected_hour_12 = st.selectbox(
            "🕐 Hour",
            hour_options_12,
            index=hour_options_12.index(default_hour_12),
            key=f"{key_prefix}_hour_12",
        )

    with c2:
        selected_minute = st.selectbox(
            "⏱ Minute",
            minute_options,
            index=minute_options.index(closest_minute),
            format_func=lambda x: f"{x:02d}",
            key=f"{key_prefix}_minute",
        )

    with c3:
        selected_ampm = st.selectbox(
            "🌗 AM / PM",
            ["AM", "PM"],
            index=0 if default_ampm == "AM" else 1,
            key=f"{key_prefix}_ampm",
        )

    hour_24 = selected_hour_12 % 12
    if selected_ampm == "PM":
        hour_24 += 12

    display_12 = f"{selected_hour_12:02d}:{selected_minute:02d} {selected_ampm}"
    display_24 = f"{hour_24:02d}:{selected_minute:02d}"

    st.info(f"✅ Selected Time: {display_12}  |  24H Format: {display_24}")

    return int(hour_24), int(selected_minute)


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


def verify_user_credentials(db: dict, username: str, password: str) -> tuple[bool, str, dict]:
    users = db.get("users", {})

    if username not in users:
        return False, "User not found.", {}

    user_record = users[username]

    if not verify_password(user_record, password):
        return False, "Invalid password.", user_record

    if is_user_blocked_for_month(db, username) and not is_management_user(user_record):
        st.session_state[SESSION_LOGIN_BLOCKED_MESSAGE] = (
            "⛔ تم إيقاف دخول التشغيل اليومي لهذا الموظف خلال هذا الشهر.\n"
            "يرجى مراجعة المدير للحصول على تصريح."
        )
        return False, "Daily operations access is blocked.", user_record

    return True, "Credentials verified.", user_record


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
    branch_name: str = "",
) -> tuple[bool, str]:
    ok, message, user_record = verify_user_credentials(db, username, password)
    if not ok:
        return False, message

    late_minutes = calculate_late_minutes(shift_name, arrival_hour, arrival_minute)
    current_late_count = get_user_month_late_count(db, username)
    next_late_count = current_late_count + 1 if late_minutes > 0 else current_late_count

    if late_minutes > 0 and not late_acknowledged:
        warning_message = get_late_warning_message(next_late_count, late_minutes)
        st.session_state[SESSION_PENDING_LATE_WARNING] = warning_message
        st.session_state[SESSION_PENDING_LOGIN_PAYLOAD] = {
            "username": username,
            "password": password,
            "shift_name": shift_name,
            "arrival_hour": int(arrival_hour),
            "arrival_minute": int(arrival_minute),
            "branch_name": branch_name,
        }
        return False, "Late acknowledgement required."

    if late_minutes > 0:
        set_user_month_late_count(db, username, next_late_count)

        add_user_warning(
            db,
            username,
            (
                f"تأخير رقم {next_late_count} خلال شهر {get_current_month_key()} "
                f"بمقدار {late_minutes} دقيقة في شفت {shift_name}"
            ),
        )

        if next_late_count == 3:
            add_monthly_late_penalty_if_needed(db, username)

        if next_late_count >= int(MONTHLY_LATE_BLOCK_AT):
            set_user_blocked_for_month(db, username, True)
            append_attendance_record(
                db=db,
                username=username,
                shift_name=shift_name,
                arrival_hour=arrival_hour,
                arrival_minute=arrival_minute,
                late_minutes=late_minutes,
                status="blocked_after_late",
                branch_name=branch_name,
            )
            persist_auth_changes(db)
            st.session_state[SESSION_LOGIN_BLOCKED_MESSAGE] = get_late_warning_message(next_late_count, late_minutes)
            return False, "Daily operations access is blocked."

        append_attendance_record(
            db=db,
            username=username,
            shift_name=shift_name,
            arrival_hour=arrival_hour,
            arrival_minute=arrival_minute,
            late_minutes=late_minutes,
            status="late",
            branch_name=branch_name,
        )
        persist_auth_changes(db)

    else:
        append_attendance_record(
            db=db,
            username=username,
            shift_name=shift_name,
            arrival_hour=arrival_hour,
            arrival_minute=arrival_minute,
            late_minutes=0,
            status="on_time",
            branch_name=branch_name,
        )
        persist_auth_changes(db)

    st.session_state[SESSION_LOGGED_IN] = True
    st.session_state[SESSION_USER] = username
    st.session_state[SESSION_ROLE] = user_record.get("role", "user")
    st.session_state[SESSION_ATTENDANCE_SHIFT] = shift_name
    st.session_state[SESSION_ATTENDANCE_TIME] = f"{int(arrival_hour):02d}:{int(arrival_minute):02d}"
    st.session_state[SESSION_SHIFT] = shift_name
    st.session_state[SESSION_BRANCH] = branch_name

    restore_user_drafts(db, username)
    log_auth_event(db, username, "Login")

    clear_pending_login_flow()

    return True, "Login successful."


def logout_user(db: dict) -> None:
    username = get_current_username() or "unknown"

    sync_user_drafts(db)
    log_auth_event(db, username, "Logout")
    persist_auth_changes(db)

    clear_user_session()


# =====================================================
# UI helpers
# =====================================================
def render_attendance_step_for_selected_user(db: dict) -> None:
    pending_username = st.session_state.get(SESSION_PENDING_ATTENDANCE_USER, "")
    pending_password = st.session_state.get(SESSION_PENDING_ATTENDANCE_PASSWORD, "")

    if not pending_username:
        return

    st.markdown("## 🕒 Attendance Confirmation")
    st.caption("أكمل بيانات الحضور قبل الدخول إلى النظام")

    render_attendance_clock_widget()

    st.success(f"👋 أهلاً {pending_username}")
    st.write("يرجى اختيار الفرع، الشيفت، ووقت الحضور بشكل واضح قبل الدخول.")

    branches = db.get("branches", []) or ["No Branch"]

    c1, c2 = st.columns(2)
    with c1:
        branch_name = st.selectbox(
            "📍 Select Branch",
            branches,
            key="attendance_branch_after_login",
        )

    shift_options = list(SHIFT_START_TIMES.keys())
    with c2:
        shift_name = st.selectbox(
            "🧭 Select Shift",
            shift_options,
            key="attendance_shift_after_login",
        )

    shift_defaults = SHIFT_START_TIMES.get(shift_name, SHIFT_START_TIMES["Morning"])

    arrival_hour, arrival_minute = render_professional_time_picker(
        title="⏰ Arrival Time",
        default_hour_24=int(shift_defaults["hour"]),
        default_minute=int(shift_defaults["minute"]),
        key_prefix="attendance_after_login",
    )

    pending_warning = st.session_state.get(SESSION_PENDING_LATE_WARNING)
    pending_payload = st.session_state.get(SESSION_PENDING_LOGIN_PAYLOAD)

    if pending_warning and pending_payload:
        st.warning(pending_warning)
        late_acknowledged = st.checkbox(
            "I have read and accepted this warning.",
            key="late_warning_ack_checkbox_after_login",
        )

        b1, b2 = st.columns(2)

        with b1:
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
                        branch_name=pending_payload.get("branch_name", branch_name),
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        if message == "Daily operations access is blocked.":
                            st.error(st.session_state.get(SESSION_LOGIN_BLOCKED_MESSAGE, message))
                        else:
                            st.error(f"❌ {message}")

        with b2:
            if st.button("⬅️ Back To Login", use_container_width=True):
                clear_pending_login_flow()
                st.rerun()

        return

    b1, b2 = st.columns(2)

    with b1:
        if st.button("🚀 Enter System", use_container_width=True):
            success, message = login_user(
                db=db,
                username=pending_username,
                password=pending_password,
                shift_name=shift_name,
                arrival_hour=int(arrival_hour),
                arrival_minute=int(arrival_minute),
                late_acknowledged=False,
                branch_name=branch_name,
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                if message == "Late acknowledgement required.":
                    st.rerun()
                elif message == "Daily operations access is blocked.":
                    st.error(st.session_state.get(SESSION_LOGIN_BLOCKED_MESSAGE, message))
                else:
                    st.error(f"❌ {message}")

    with b2:
        if st.button("⬅️ Back To Login", use_container_width=True):
            clear_pending_login_flow()
            st.rerun()


# =====================================================
# UI
# =====================================================
def render_login_screen(db: dict) -> None:
    st.title("🔐 NMS Enterprise Access")

    users = list(db.get("users", {}).keys())
    if not users:
        st.error("No users found in database. Please create an admin user first.")
        st.stop()

    blocked_message = st.session_state.get(SESSION_LOGIN_BLOCKED_MESSAGE)
    if blocked_message:
        st.error(blocked_message)

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        st.write("### 🔑 Secure Login")

        pending_attendance_user = st.session_state.get(SESSION_PENDING_ATTENDANCE_USER)
        if pending_attendance_user:
            render_attendance_step_for_selected_user(db)
            st.stop()

        username = st.selectbox("Select Your Account", users)
        password = st.text_input("Enter Password", type="password")

        user_record = get_user_record(db, username)
        needs_attendance_after_login = requires_post_login_attendance_step(user_record)

        if not needs_attendance_after_login:
            st.write("### 🕒 Attendance Confirmation")

            branches = db.get("branches", []) or ["No Branch"]

            c_branch, c_shift = st.columns(2)
            with c_branch:
                branch_name = st.selectbox("📍 Select Branch", branches)

            with c_shift:
                shift_name = st.selectbox("🧭 Select Shift", list(SHIFT_START_TIMES.keys()))

            shift_defaults = SHIFT_START_TIMES.get(shift_name, SHIFT_START_TIMES["Morning"])

            arrival_hour, arrival_minute = render_professional_time_picker(
                title="⏰ Arrival Time",
                default_hour_24=int(shift_defaults["hour"]),
                default_minute=int(shift_defaults["minute"]),
                key_prefix="direct_login_attendance",
            )

            pending_warning = st.session_state.get(SESSION_PENDING_LATE_WARNING)
            pending_payload = st.session_state.get(SESSION_PENDING_LOGIN_PAYLOAD)

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
                            branch_name=pending_payload.get("branch_name", ""),
                        )

                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            if message == "Daily operations access is blocked.":
                                st.error(st.session_state.get(SESSION_LOGIN_BLOCKED_MESSAGE, message))
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
                        branch_name=branch_name,
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        if message == "Late acknowledgement required.":
                            st.rerun()
                        elif message == "Daily operations access is blocked.":
                            st.error(st.session_state.get(SESSION_LOGIN_BLOCKED_MESSAGE, message))
                        else:
                            st.error(f"❌ {message}")

        else:
            st.info("بعد التحقق من الحساب، ستظهر لك خطوة اختيار الفرع والشيفت ووقت الحضور بشكل احترافي.")

            if st.button("➡️ Continue", use_container_width=True):
                ok, message, verified_user = verify_user_credentials(db, username, password)

                if ok:
                    st.session_state[SESSION_PENDING_ATTENDANCE_USER] = username
                    st.session_state[SESSION_PENDING_ATTENDANCE_PASSWORD] = password
                    st.session_state[SESSION_PENDING_ATTENDANCE_ROLE] = verified_user.get("role", "")
                    st.rerun()
                else:
                    if message == "Daily operations access is blocked.":
                        st.error(st.session_state.get(SESSION_LOGIN_BLOCKED_MESSAGE, message))
                    else:
                        st.error(f"❌ {message}")

    st.stop()
