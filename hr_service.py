import base64
from datetime import date

import pandas as pd
import streamlit as st

from auth_service import (
    get_current_month_key,
    get_current_role,
    get_current_username,
    set_user_blocked_for_month,
    set_user_month_late_count,
)
from constants import (
    DEFAULT_BIRTH_DATE,
    DEFAULT_HIRING_DATE,
    HR_FORM_TO_DB_KEY,
    HR_RECORD_KEYS,
    HR_RECORD_LABELS,
    PAYOUT_METHOD_LABELS,
    PAYOUT_METHOD_OPTIONS,
    ROLE_ADMIN,
    ROLE_LABELS,
    ROLE_MANAGER,
    ROLE_USER,
    SESSION_ACTIVE_DB,
)
from database import create_user, save_db


# =====================================================
# Dynamic Role Helpers
# =====================================================
def _normalize_role_value(role_value: str | None) -> str:
    return str(role_value or "").strip().lower()


def get_dynamic_role_options(db: dict) -> list[str]:
    users = db.get("users", {}) or {}

    role_candidates = set()

    try:
        from constants import ROLE_OPTIONS
        role_candidates.update(ROLE_OPTIONS)
    except Exception:
        pass

    try:
        from constants import ROLE_LABELS as _ROLE_LABELS
        role_candidates.update(_ROLE_LABELS.keys())
    except Exception:
        pass

    try:
        from constants import ROLE_TASK_ACCESS
        role_candidates.update(ROLE_TASK_ACCESS.keys())
    except Exception:
        pass

    for _, user_data in users.items():
        role_value = _normalize_role_value(user_data.get("role"))
        if role_value:
            role_candidates.add(role_value)

    role_candidates.add(ROLE_ADMIN)
    role_candidates.add(ROLE_MANAGER)
    role_candidates.add(ROLE_USER)

    return sorted(role_candidates)


def format_role_label(role_value: str) -> str:
    role_value = _normalize_role_value(role_value)

    if role_value in ROLE_LABELS:
        return ROLE_LABELS[role_value]

    return role_value.replace("_", " ").title() if role_value else "Unknown"


# =====================================================
# Helpers
# =====================================================
def is_admin_or_manager() -> bool:
    current_role = _normalize_role_value(get_current_role())
    return current_role in [ROLE_ADMIN, ROLE_MANAGER]


def get_manageable_usernames(db: dict) -> list[str]:
    users = db.get("users", {})

    if is_admin_or_manager():
        return list(users.keys())

    current_username = get_current_username()
    if current_username and current_username in users:
        return [current_username]

    return []


def can_create_employee() -> bool:
    return is_admin_or_manager()


def can_rename_username() -> bool:
    return is_admin_or_manager()


def can_delete_employee() -> bool:
    return is_admin_or_manager()


def can_edit_role() -> bool:
    return is_admin_or_manager()


def can_manage_attendance_controls() -> bool:
    return is_admin_or_manager()


def can_edit_salary_and_payout() -> bool:
    return is_admin_or_manager()


def can_add_financial_records() -> bool:
    return is_admin_or_manager()


def get_current_month_late_count(db: dict, username: str) -> int:
    month_key = get_current_month_key()
    return int(db.get("late_tracking", {}).get(month_key, {}).get(username, 0))


def is_current_month_blocked(db: dict, username: str) -> bool:
    month_key = get_current_month_key()
    return bool(db.get("blocked_users", {}).get(month_key, {}).get(username, False))


def remove_user_month_block(db: dict, username: str) -> None:
    set_user_blocked_for_month(db, username, False)


def reset_user_month_late_count(db: dict, username: str) -> None:
    set_user_month_late_count(db, username, 0)


def ensure_user_defaults(user: dict) -> None:
    defaults = {
        "full_name": "",
        "pass": "",
        "phone": "",
        "email": "",
        "national_id": "",
        "address": "",
        "qualification": "",
        "hiring_date": DEFAULT_HIRING_DATE,
        "birth_date": DEFAULT_BIRTH_DATE,
        "employee_code": "",
        "salary": 0.0,
        "salary_basic": 0.0,
        "transport_allowance": 0.0,
        "communication_allowance": 0.0,
        "other_allowance": 0.0,
        "bank_name": "",
        "bank_account_number": "",
        "wallet_number": "",
        "payout_method": "bank",
        "photo": "",
        "id_card": "",
        "bonus": [],
        "deductions": [],
        "overtime": [],
        "extra_leaves": [],
        "advances": [],
        "late_penalties": [],
        "absence_penalties": [],
        "warnings": [],
        "role": ROLE_USER,
        "job_title": "",
    }

    for key, default_value in defaults.items():
        user.setdefault(key, default_value)

    if not user.get("job_title"):
        role_value = user.get("role", ROLE_USER)
        user["job_title"] = format_role_label(role_value)

    if not user.get("employee_code"):
        national_id = str(user.get("national_id", "") or "").strip()
        user["employee_code"] = national_id if national_id else ""


def safe_decode_image(image_b64: str):
    if not image_b64:
        return None

    try:
        return base64.b64decode(image_b64)
    except Exception:
        return None


def save_uploaded_image(uploaded_file) -> str:
    return base64.b64encode(uploaded_file.getvalue()).decode()


def get_safe_hiring_date(user: dict):
    raw_value = user.get("hiring_date", DEFAULT_HIRING_DATE)
    try:
        return date.fromisoformat(raw_value)
    except Exception:
        return date.fromisoformat(DEFAULT_HIRING_DATE)


def get_safe_birth_date(user: dict):
    raw_value = user.get("birth_date", DEFAULT_BIRTH_DATE)
    try:
        return date.fromisoformat(raw_value)
    except Exception:
        return date.fromisoformat(DEFAULT_BIRTH_DATE)


def get_role_display(role_value: str) -> str:
    return format_role_label(role_value)


def get_payout_method_display(method_value: str) -> str:
    return PAYOUT_METHOD_LABELS.get(method_value, str(method_value).replace("_", " ").title())


def normalize_financial_records(records: list) -> list:
    normalized = []

    for record in records or []:
        normalized.append(
            {
                "date": record.get("date", "-"),
                "amount": float(record.get("amount", record.get("val", 0)) or 0),
                "note": record.get("note", "-"),
            }
        )

    return normalized


def persist_db(db: dict, success_message: str | None = None) -> None:
    save_db(db)
    if success_message:
        st.success(success_message)
    st.rerun()


def rename_username_in_db(db: dict, old_username: str, new_username: str) -> tuple[bool, str]:
    old_username = old_username.strip()
    new_username = new_username.strip()

    if not old_username:
        return False, "Old username is invalid."

    if not new_username:
        return False, "New username is required."

    if old_username == "admin":
        return False, "Admin username cannot be renamed."

    if old_username not in db.get("users", {}):
        return False, "Old username was not found."

    if new_username != old_username and new_username in db.get("users", {}):
        return False, "New username already exists."

    if new_username == old_username:
        return False, "New username matches current username."

    db["users"][new_username] = db["users"].pop(old_username)

    if old_username in db.get("drafts", {}):
        db["drafts"][new_username] = db["drafts"].pop(old_username)

    if old_username in db.get("training_records", {}):
        db["training_records"][new_username] = db["training_records"].pop(old_username)

    for log_item in db.get("logs", []):
        if log_item.get("user") == old_username:
            log_item["user"] = new_username

    for history_item in db.get("history", []):
        if history_item.get("staff_username") == old_username:
            history_item["staff_username"] = new_username

    save_db(db)
    return True, "Username updated successfully."


def calculate_salary_breakdown(user: dict) -> dict:
    salary_basic = float(user.get("salary_basic", 0) or 0)
    transport_allowance = float(user.get("transport_allowance", 0) or 0)
    communication_allowance = float(user.get("communication_allowance", 0) or 0)
    other_allowance = float(user.get("other_allowance", 0) or 0)

    total_fixed = (
        salary_basic
        + transport_allowance
        + communication_allowance
        + other_allowance
    )

    total_bonus = sum(float(item.get("amount", 0) or 0) for item in user.get("bonus", []))
    total_overtime = sum(float(item.get("amount", 0) or 0) for item in user.get("overtime", []))

    total_deductions = sum(float(item.get("amount", 0) or 0) for item in user.get("deductions", []))
    total_advances = sum(float(item.get("amount", 0) or 0) for item in user.get("advances", []))
    total_late_penalties = sum(float(item.get("amount", 0) or 0) for item in user.get("late_penalties", []))
    total_absence_penalties = sum(float(item.get("amount", 0) or 0) for item in user.get("absence_penalties", []))

    gross_salary = total_fixed + total_bonus + total_overtime
    total_withheld = total_deductions + total_advances + total_late_penalties + total_absence_penalties
    net_salary = gross_salary - total_withheld

    return {
        "salary_basic": salary_basic,
        "transport_allowance": transport_allowance,
        "communication_allowance": communication_allowance,
        "other_allowance": other_allowance,
        "total_fixed": total_fixed,
        "total_bonus": total_bonus,
        "total_overtime": total_overtime,
        "total_deductions": total_deductions,
        "total_advances": total_advances,
        "total_late_penalties": total_late_penalties,
        "total_absence_penalties": total_absence_penalties,
        "gross_salary": gross_salary,
        "total_withheld": total_withheld,
        "net_salary": net_salary,
    }


# =====================================================
# Create Employee
# =====================================================
def render_create_employee_section(db: dict) -> None:
    if not can_create_employee():
        return

    st.markdown("## ➕ Create New Employee")

    role_options = get_dynamic_role_options(db)

    with st.expander("Add New Employee", expanded=False):
        new_username = st.text_input("Username", key="create_username")
        new_password = st.text_input("Password", type="password", key="create_password")
        new_full_name = st.text_input("Full Name", key="create_full_name")
        new_role = st.selectbox(
            "Role",
            role_options,
            format_func=get_role_display,
            key="create_role",
        )
        new_job_title = st.text_input(
            "Job Title",
            value=get_role_display(new_role),
            key="create_job_title",
        )

        if st.button("✅ Create Employee", use_container_width=True):
            success, message = create_user(
                username=new_username,
                password=new_password,
                full_name=new_full_name,
                role=new_role,
                job_title=new_job_title,
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


# =====================================================
# Sections
# =====================================================
def render_profile_images(users: dict, target: str, user: dict) -> None:
    st.markdown("## 📌 Employee Profile")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🖼 Profile Photo")

        photo_bytes = safe_decode_image(user.get("photo", ""))
        if photo_bytes:
            st.image(photo_bytes, width=150)
        else:
            st.info("No profile photo uploaded.")

        new_photo = st.file_uploader(
            "Upload Profile Photo",
            type=["png", "jpg", "jpeg"],
            key=f"profile_photo_{target}",
        )

        if new_photo and st.button("💾 Save Photo", key=f"save_photo_{target}"):
            users[target]["photo"] = save_uploaded_image(new_photo)
            persist_db(st.session_state[SESSION_ACTIVE_DB], "Photo Updated")

    with col2:
        st.markdown("### 🪪 ID Card")

        id_card_bytes = safe_decode_image(user.get("id_card", ""))
        if id_card_bytes:
            st.image(id_card_bytes, width=200)
        else:
            st.info("No ID card uploaded.")

        id_card = st.file_uploader(
            "Upload ID Card",
            type=["png", "jpg", "jpeg"],
            key=f"id_card_upload_{target}",
        )

        if id_card and st.button("💾 Save ID Card", key=f"save_id_card_{target}"):
            users[target]["id_card"] = save_uploaded_image(id_card)
            persist_db(st.session_state[SESSION_ACTIVE_DB], "ID Card Saved")


def render_username_management(target: str, db: dict) -> None:
    st.divider()
    st.markdown("## 🔑 Username Management")

    st.text_input(
        "Current Username",
        value=target,
        disabled=True,
        key=f"current_username_{target}",
    )

    if not can_rename_username():
        st.info("You can view your username only.")
        return

    if target == "admin":
        st.info("Admin username cannot be changed.")
        return

    new_username = st.text_input(
        "New Username",
        value=target,
        key=f"rename_username_{target}",
    )

    if st.button("🔄 Rename Username", key=f"rename_username_btn_{target}"):
        success, message = rename_username_in_db(db, target, new_username)

        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def render_personal_details(users: dict, target: str, user: dict, db: dict) -> None:
    st.divider()
    st.markdown("## 📝 Personal Details")

    role_options = get_dynamic_role_options(db)
    current_role = user.get("role", ROLE_USER)

    if current_role not in role_options:
        role_options = sorted(set(role_options + [current_role]))

    current_role_index = role_options.index(current_role) if current_role in role_options else 0

    full_name = st.text_input("Full Name", value=user.get("full_name", ""), key=f"edit_full_name_{target}")
    password = st.text_input("Password", value=user.get("pass", ""), key=f"edit_password_{target}")

    if can_edit_role():
        role_value = st.selectbox(
            "Role",
            role_options,
            index=current_role_index,
            format_func=get_role_display,
            key=f"edit_role_{target}",
        )
    else:
        role_value = current_role
        st.text_input(
            "Role",
            value=get_role_display(role_value),
            disabled=True,
            key=f"edit_role_readonly_{target}",
        )

    job_title = st.text_input("Job Title", value=user.get("job_title", ""), key=f"edit_job_title_{target}")
    employee_code = st.text_input("Employee Code", value=user.get("employee_code", ""), key=f"edit_employee_code_{target}")
    birth_date = st.date_input(
        "Birth Date",
        value=get_safe_birth_date(user),
        key=f"edit_birth_date_{target}",
    )

    phone = st.text_input("Phone", value=user.get("phone", ""), key=f"edit_phone_{target}")
    email = st.text_input("Email", value=user.get("email", ""), key=f"edit_email_{target}")
    national_id = st.text_input("National ID", value=user.get("national_id", ""), key=f"edit_national_id_{target}")
    address = st.text_area("Address", value=user.get("address", ""), key=f"edit_address_{target}")
    qualification = st.text_input("Qualification", value=user.get("qualification", ""), key=f"edit_qualification_{target}")

    hiring_date = st.date_input(
        "Work Start Date",
        value=get_safe_hiring_date(user),
        key=f"edit_hiring_date_{target}",
    )

    if st.button("💾 Save Employee Data", key=f"save_employee_data_{target}"):
        cleaned_national_id = national_id.strip()
        cleaned_employee_code = employee_code.strip() or cleaned_national_id

        users[target].update(
            {
                "full_name": full_name.strip(),
                "pass": password,
                "role": role_value,
                "job_title": job_title.strip() or get_role_display(role_value),
                "employee_code": cleaned_employee_code,
                "birth_date": str(birth_date),
                "phone": phone.strip(),
                "email": email.strip(),
                "national_id": cleaned_national_id,
                "address": address.strip(),
                "qualification": qualification.strip(),
                "hiring_date": str(hiring_date),
            }
        )

        persist_db(db, "✅ Employee Updated")


def render_salary_and_payout_section(users: dict, target: str, user: dict, db: dict) -> None:
    st.divider()
    st.markdown("## 💰 Salary Structure & Payout")

    if not can_edit_salary_and_payout():
        st.info("You can view salary summary only.")
        return

    col1, col2 = st.columns(2)

    with col1:
        salary_basic = st.number_input(
            "Basic Salary",
            min_value=0.0,
            value=float(user.get("salary_basic", 0) or 0),
            step=100.0,
            key=f"salary_basic_{target}",
        )
        transport_allowance = st.number_input(
            "Transport Allowance",
            min_value=0.0,
            value=float(user.get("transport_allowance", 0) or 0),
            step=50.0,
            key=f"transport_allowance_{target}",
        )
        communication_allowance = st.number_input(
            "Communication Allowance",
            min_value=0.0,
            value=float(user.get("communication_allowance", 0) or 0),
            step=50.0,
            key=f"communication_allowance_{target}",
        )
        other_allowance = st.number_input(
            "Other Allowance",
            min_value=0.0,
            value=float(user.get("other_allowance", 0) or 0),
            step=50.0,
            key=f"other_allowance_{target}",
        )

    with col2:
        payout_method = st.selectbox(
            "Payout Method",
            PAYOUT_METHOD_OPTIONS,
            index=PAYOUT_METHOD_OPTIONS.index(user.get("payout_method", "bank"))
            if user.get("payout_method", "bank") in PAYOUT_METHOD_OPTIONS
            else 0,
            format_func=get_payout_method_display,
            key=f"payout_method_{target}",
        )

        bank_name = st.text_input("Bank Name", value=user.get("bank_name", ""), key=f"bank_name_{target}")
        bank_account_number = st.text_input(
            "Bank Account Number / IBAN",
            value=user.get("bank_account_number", ""),
            key=f"bank_account_number_{target}",
        )
        wallet_number = st.text_input(
            "Wallet Number",
            value=user.get("wallet_number", ""),
            key=f"wallet_number_{target}",
        )

    if st.button("💾 Save Salary & Payout", key=f"save_salary_payout_{target}"):
        total_salary = (
            float(salary_basic or 0)
            + float(transport_allowance or 0)
            + float(communication_allowance or 0)
            + float(other_allowance or 0)
        )

        users[target].update(
            {
                "salary_basic": float(salary_basic or 0),
                "transport_allowance": float(transport_allowance or 0),
                "communication_allowance": float(communication_allowance or 0),
                "other_allowance": float(other_allowance or 0),
                "salary": total_salary,
                "payout_method": payout_method,
                "bank_name": bank_name.strip(),
                "bank_account_number": bank_account_number.strip(),
                "wallet_number": wallet_number.strip(),
            }
        )

        persist_db(db, "✅ Salary & Payout Updated")


def render_salary_summary(user: dict) -> None:
    st.divider()
    st.markdown("## 📈 Salary Summary")

    summary = calculate_salary_breakdown(user)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Fixed Salary", f"{summary['total_fixed']:,.2f}")
    with c2:
        st.metric("Gross Salary", f"{summary['gross_salary']:,.2f}")
    with c3:
        st.metric("Net Salary", f"{summary['net_salary']:,.2f}")

    df = pd.DataFrame(
        [
            {"Item": "Basic Salary", "Value": summary["salary_basic"]},
            {"Item": "Transport Allowance", "Value": summary["transport_allowance"]},
            {"Item": "Communication Allowance", "Value": summary["communication_allowance"]},
            {"Item": "Other Allowance", "Value": summary["other_allowance"]},
            {"Item": "Total Bonus", "Value": summary["total_bonus"]},
            {"Item": "Total Overtime", "Value": summary["total_overtime"]},
            {"Item": "Total Deductions", "Value": summary["total_deductions"]},
            {"Item": "Total Advances", "Value": summary["total_advances"]},
            {"Item": "Late Penalties", "Value": summary["total_late_penalties"]},
            {"Item": "Absence Penalties", "Value": summary["total_absence_penalties"]},
            {"Item": "Total Withheld", "Value": summary["total_withheld"]},
            {"Item": "Net Salary", "Value": summary["net_salary"]},
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Value": st.column_config.NumberColumn("Value", format="%.2f"),
        },
    )


def render_warning_section(users: dict, target: str, user: dict, db: dict) -> None:
    st.divider()
    st.markdown("## 🚨 Warnings")

    current_warnings = user.get("warnings", [])
    if current_warnings:
        warnings_df = pd.DataFrame(
            [
                {
                    "date": item.get("date", "-"),
                    "note": item.get("note", "-"),
                }
                for item in current_warnings
            ]
        )
        st.dataframe(warnings_df, use_container_width=True)
    else:
        st.info("No warnings recorded.")

    if is_admin_or_manager():
        warning_note = st.text_area("Add Warning Note", key=f"warning_note_{target}")

        if st.button("➕ Add Warning", key=f"add_warning_{target}"):
            if warning_note.strip():
                users[target].setdefault("warnings", [])
                users[target]["warnings"].append(
                    {
                        "date": str(date.today()),
                        "note": warning_note.strip(),
                    }
                )
                persist_db(db, "✅ Warning Added")
            else:
                st.warning("Please write a warning note first.")


def render_attendance_control_section(users: dict, target: str, user: dict, db: dict) -> None:
    st.divider()
    st.markdown("## ⏰ Attendance Control")

    month_key = get_current_month_key()
    late_count = get_current_month_late_count(db, target)
    blocked_now = is_current_month_blocked(db, target)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Current Month", month_key)
    with c2:
        st.metric("Late Count", late_count)
    with c3:
        st.metric("Blocked", "Yes" if blocked_now else "No")

    attendance_rows = db.get("attendance_records", {}).get(month_key, {}).get(target, [])
    if attendance_rows:
        df_attendance = pd.DataFrame(attendance_rows)
        st.dataframe(
            df_attendance,
            use_container_width=True,
            column_config={
                "late_minutes": st.column_config.NumberColumn("Late Minutes", format="%d"),
                "date": "Date",
                "time": "Time",
                "shift": "Shift",
                "status": "Status",
                "created_at": "Created At",
            },
        )
    else:
        st.info("No attendance records for this month.")

    if not can_manage_attendance_controls():
        st.info("You can view your attendance status only.")
        return

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("🔓 Unblock For Current Month", key=f"unblock_user_{target}", use_container_width=True):
            remove_user_month_block(db, target)
            users[target].setdefault("warnings", [])
            users[target]["warnings"].append(
                {
                    "date": str(date.today()),
                    "note": f"تم فك حظر التشغيل اليومي للشهر الحالي بواسطة الإدارة ({get_current_username()}).",
                }
            )
            persist_db(db, "✅ User unblocked for current month")

    with col_b:
        if st.button("🔄 Reset Late Count", key=f"reset_late_count_{target}", use_container_width=True):
            reset_user_month_late_count(db, target)
            users[target].setdefault("warnings", [])
            users[target]["warnings"].append(
                {
                    "date": str(date.today()),
                    "note": f"تم تصفير عداد التأخير للشهر الحالي بواسطة الإدارة ({get_current_username()}).",
                }
            )
            persist_db(db, "✅ Late count reset for current month")


def render_financial_entry_form(user: dict, db: dict, target: str) -> None:
    st.divider()
    st.markdown("## 💰 Financial History")

    if not can_add_financial_records():
        st.info("You can view your financial history only.")
        return

    record_type = st.radio(
        "Record Type",
        list(HR_FORM_TO_DB_KEY.keys()),
        horizontal=True,
        key=f"record_type_{target}",
    )

    amount = st.number_input(
        "Amount",
        min_value=0.0,
        step=10.0,
        key=f"record_amount_{target}",
    )

    note = st.text_input("Reason / Note", key=f"record_note_{target}")

    if st.button("➕ Add Financial Record", key=f"add_financial_record_{target}"):
        target_key = HR_FORM_TO_DB_KEY[record_type]
        user.setdefault(target_key, [])
        user[target_key].append(
            {
                "date": str(date.today()),
                "amount": amount,
                "note": note.strip(),
            }
        )

        persist_db(db, "✅ Record Added")


def render_records_history(user: dict) -> None:
    st.divider()
    st.markdown("## 📊 Employee Records History")

    for category in HR_RECORD_KEYS:
        label = HR_RECORD_LABELS.get(category, category.title())
        st.markdown(f"### 🔹 {label.upper()}")

        records = normalize_financial_records(user.get(category, []))

        if not records:
            st.info("No Records")
            continue

        df = pd.DataFrame(records)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                "date": "Date",
                "note": "Note",
            },
        )

    extra_sections = [
        ("ADVANCES", user.get("advances", [])),
        ("LATE PENALTIES", user.get("late_penalties", [])),
        ("ABSENCE PENALTIES", user.get("absence_penalties", [])),
    ]

    for title, records_source in extra_sections:
        st.markdown(f"### 🔹 {title}")
        records = normalize_financial_records(records_source)

        if not records:
            st.info("No Records")
            continue

        df = pd.DataFrame(records)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                "date": "Date",
                "note": "Note",
            },
        )


def render_delete_employee(users: dict, target: str, db: dict) -> None:
    st.divider()

    if not can_delete_employee():
        return

    if target == "admin":
        st.info("Admin account cannot be deleted from here.")
        return

    st.markdown("## ⚠️ Delete Employee")
    confirm_delete = st.checkbox(
        f"I confirm deleting employee: {target}",
        key=f"delete_confirm_{target}",
    )

    if confirm_delete and st.button("🗑 Delete Employee", type="primary", key=f"delete_employee_{target}"):
        del users[target]

        if target in db.get("drafts", {}):
            del db["drafts"][target]

        if target in db.get("training_records", {}):
            del db["training_records"][target]

        if "attendance_records" in db:
            for month_key in list(db["attendance_records"].keys()):
                if target in db["attendance_records"].get(month_key, {}):
                    del db["attendance_records"][month_key][target]

        if "late_tracking" in db:
            for month_key in list(db["late_tracking"].keys()):
                if target in db["late_tracking"].get(month_key, {}):
                    del db["late_tracking"][month_key][target]

        if "blocked_users" in db:
            for month_key in list(db["blocked_users"].keys()):
                if target in db["blocked_users"].get(month_key, {}):
                    del db["blocked_users"][month_key][target]

        persist_db(db, "Employee Deleted")


# =====================================================
# Main UI
# =====================================================
def hr_management_ui(db: dict) -> None:
    st.session_state[SESSION_ACTIVE_DB] = db

    st.title("👥 Employee Management System")

    render_create_employee_section(db)

    users = db.get("users", {})
    if not users:
        st.warning("No Employees Found")
        return

    st.divider()
    st.markdown("## 👤 Manage Employee")

    manageable_usernames = get_manageable_usernames(db)
    if not manageable_usernames:
        st.warning("No employee profile available.")
        return

    if is_admin_or_manager():
        target = st.selectbox("Select Employee", manageable_usernames)
    else:
        target = manageable_usernames[0]
        st.text_input("Employee Username", value=target, disabled=True)

    if not target:
        return

    user = users[target]
    ensure_user_defaults(user)

    st.info(
        f"Role: {get_role_display(user.get('role', ROLE_USER))} | "
        f"Job Title: {user.get('job_title', '-')} | "
        f"Employee Code: {user.get('employee_code', '-') or '-'}"
    )

    render_username_management(target, db)
    render_profile_images(users, target, user)
    render_personal_details(users, target, user, db)
    render_salary_and_payout_section(users, target, user, db)
    render_salary_summary(user)
    render_warning_section(users, target, user, db)
    render_attendance_control_section(users, target, user, db)
    render_financial_entry_form(user, db, target)
    render_records_history(user)
    render_delete_employee(users, target, db)
