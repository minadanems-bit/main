import streamlit as st
from database import save_db
import base64
from datetime import date


# =====================================================
# HR MANAGEMENT SYSTEM (PRO VERSION)
# =====================================================

def hr_management_ui(db):

    st.title("👥 Employee Management System")

    users = db["users"]

    if not users:
        st.warning("No Employees Found")
        return

    # ==================================================
    # SELECT EMPLOYEE
    # ==================================================
    target = st.selectbox(
        "Select Employee",
        list(users.keys())
    )

    if not target:
        return

    user = users[target]

    st.divider()

    # ==================================================
    # PROFILE SECTION
    # ==================================================
    st.markdown("## 📌 Employee Profile")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🖼 Profile Photo")

        if user.get("photo"):
            st.image(base64.b64decode(user["photo"]), width=150)

        new_photo = st.file_uploader("Upload Profile Photo", type=["png","jpg","jpeg"])

        if new_photo and st.button("💾 Save Photo"):
            users[target]["photo"] = base64.b64encode(new_photo.getvalue()).decode()
            save_db(db)
            st.success("Photo Updated")
            st.rerun()

    with col2:
        st.markdown("### 🪪 ID Card")

        if user.get("id_card"):
            st.image(base64.b64decode(user["id_card"]), width=200)

        id_card = st.file_uploader("Upload ID Card", type=["png","jpg","jpeg"], key="id_card_upload")

        if id_card and st.button("💾 Save ID Card"):
            users[target]["id_card"] = base64.b64encode(id_card.getvalue()).decode()
            save_db(db)
            st.success("ID Card Saved")
            st.rerun()

    st.divider()

    # ==================================================
    # EMPLOYEE BASIC DETAILS
    # ==================================================
    st.markdown("## 📝 Personal Details")

    full_name = st.text_input("Full Name", value=user.get("full_name",""))
    password = st.text_input("Password", value=user.get("pass",""))
    phone = st.text_input("Phone", value=user.get("phone",""))
    email = st.text_input("Email", value=user.get("email",""))
    national_id = st.text_input("National ID", value=user.get("national_id",""))
    address = st.text_area("Address", value=user.get("address",""))
    qualification = st.text_input("Qualification", value=user.get("qualification",""))

    # 👇 New Important Field
    hiring_date = st.date_input(
        "Work Start Date",
        value=date.fromisoformat(user.get("hiring_date", str(date.today())))
    )

    salary = st.number_input(
        "Base Salary",
        value=float(user.get("salary",0))
    )

    if st.button("💾 Save Employee Data"):
        users[target].update({
            "full_name": full_name,
            "pass": password,
            "phone": phone,
            "email": email,
            "national_id": national_id,
            "address": address,
            "qualification": qualification,
            "hiring_date": str(hiring_date),
            "salary": salary
        })

        save_db(db)
        st.success("✅ Employee Updated")
        st.rerun()

    st.divider()

    # ==================================================
    # FINANCIAL RECORDS
    # ==================================================
    st.markdown("## 💰 Financial History")

    record_type = st.radio(
        "Record Type",
        ["Bonus","Deduction","Overtime","Extra Leave"],
        horizontal=True
    )

    amount = st.number_input("Amount", step=10.0)
    note = st.text_input("Reason / Note")

    if st.button("➕ Add Financial Record"):

        key_map = {
            "Bonus": "bonus",
            "Deduction": "deductions",
            "Overtime": "overtime",
            "Extra Leave": "extra_leaves"
        }

        key = key_map[record_type]

        users[target][key].append({
            "date": str(date.today()),
            "amount": amount,
            "note": note
        })

        save_db(db)
        st.success("✅ Record Added")

    # ==================================================
    # SHOW HISTORY
    # ==================================================
    st.divider()
    st.markdown("## 📊 Employee Records History")

    for category in ["bonus","deductions","overtime","extra_leaves"]:

        st.markdown(f"### 🔹 {category.upper()}")

        records = user.get(category, [])

        if records:
            for r in records:
                st.write(f"📅 {r['date']} | 💵 {r.get('amount',0)} | 📝 {r.get('note','-')}")
        else:
            st.info("No Records")

    st.divider()

    # ==================================================
    # DELETE EMPLOYEE
    # ==================================================
    if target != "admin":
        if st.button("🗑 Delete Employee", type="primary"):
            del users[target]
            save_db(db)
            st.warning("Employee Deleted")
            st.rerun()
