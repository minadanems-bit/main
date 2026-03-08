import base64
from datetime import date

import pandas as pd
import streamlit as st

from constants import (
    DEFAULT_HIRING_DATE,
    HR_FORM_TO_DB_KEY,
    HR_RECORD_KEYS,
    HR_RECORD_LABELS,
    ROLE_USER,
    SESSION_ACTIVE_DB,
)
from database import save_db


# =====================================================
# Helpers
# =====================================================
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
        "salary": 0.0,
        "photo": "",
        "id_card": "",
        "bonus": [],
        "deductions": [],
        "overtime": [],
        "extra_leaves": [],
        "role": ROLE_USER,
    }

    for key, default_value in defaults.items():
        if key not in user:
            user[key] = default_value


def safe_decode_image(image_b64: str):
    if not image_b64:
        return None

    try:
        return base64.b64decode(image_b64)
    except Exception:
        return None


def normalize_financial_records(records: list) -> list:
    normalized = []

    for record in records or []:
        normalized.append(
            {
                "date": record.get("date", "-"),
                "amount": record.get("amount", record.get("val", 0)),
                "note": record.get("note", "-"),
            }
        )

    return normalized


def save_uploaded_image(uploaded_file) -> str:
    return base64.b64encode(uploaded_file.getvalue()).decode()


def get_safe_hiring_date(user: dict):
    raw_value = user.get("hiring_date", DEFAULT_HIRING_DATE)
    try:
        return date.fromisoformat(raw_value)
    except Exception:
        return date.fromisoformat(DEFAULT_HIRING_DATE)


# =====================================================
# UI Sections
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
            save_db(st.session_state[SESSION_ACTIVE_DB])
            st.success("Photo Updated")
            st.rerun()

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
            save_db(st.session_state[SESSION_ACTIVE_DB])
            st.success("ID Card Saved")
            st.rerun()


def render_personal_details(users: dict, target: str, user: dict, db: dict) -> None:
    st.divider()
    st.markdown("## 📝 Personal Details")

    full_name = st.text_input("Full Name", value=user.get("full_name", ""))
    password = st.text_input("Password", value=user.get("pass", ""))
    phone = st.text_input("Phone", value=user.get("phone", ""))
    email = st.text_input("Email", value=user.get("email", ""))
    national_id = st.text_input("National ID", value=user.get("national_id", ""))
    address = st.text_area("Address", value=user.get("address", ""))
    qualification = st.text_input("Qualification", value=user.get("qualification", ""))

    hiring_date = st.date_input("Work Start Date", value=get_safe_hiring_date(user))

    salary = st.number_input(
        "Base Salary",
        min_value=0.0,
        value=float(user.get("salary", 0) or 0),
        step=100.0,
    )

    if st.button("💾 Save Employee Data"):
        users[target].update(
            {
                "full_name": full_name.strip(),
                "pass": password,
                "phone": phone.strip(),
                "email": email.strip(),
                "national_id": national_id.strip(),
                "address": address.strip(),
                "qualification": qualification.strip(),
                "hiring_date": str(hiring_date),
                "salary": salary,
            }
        )

        save_db(db)
        st.success("✅ Employee Updated")
        st.rerun()


def render_financial_entry_form(user: dict, db: dict) -> None:
    st.divider()
    st.markdown("## 💰 Financial History")

    record_type = st.radio(
        "Record Type",
        list(HR_FORM_TO_DB_KEY.keys()),
        horizontal=True,
    )

    amount = st.number_input("Amount", min_value=0.0, step=10.0)
    note = st.text_input("Reason / Note")

    if st.button("➕ Add Financial Record"):
        target_key = HR_FORM_TO_DB_KEY[record_type]
        user.setdefault(target_key, [])
        user[target_key].append(
            {
                "date": str(date.today()),
                "amount": amount,
                "note": note.strip(),
            }
        )

        save_db(db)
        st.success("✅ Record Added")
        st.rerun()


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


def render_delete_employee(users: dict, target: str, db: dict) -> None:
    st.divider()

    if target == "admin":
        st.info("Admin account cannot be deleted from here.")
        return

    st.markdown("## ⚠️ Delete Employee")
    confirm_delete = st.checkbox(f"I confirm deleting employee: {target}")

    if confirm_delete and st.button("🗑 Delete Employee", type="primary"):
        del users[target]
        save_db(db)
        st.warning("Employee Deleted")
        st.rerun()


# =====================================================
# Main UI
# =====================================================
def hr_management_ui(db: dict) -> None:
    st.session_state[SESSION_ACTIVE_DB] = db

    st.title("👥 Employee Management System")

    users = db.get("users", {})
    if not users:
        st.warning("No Employees Found")
        return

    target = st.selectbox("Select Employee", list(users.keys()))
    if not target:
        return

    user = users[target]
    ensure_user_defaults(user)

    render_profile_images(users, target, user)
    render_personal_details(users, target, user, db)
    render_financial_entry_form(user, db)
    render_records_history(user)
    render_delete_employee(users, target, db)
