import streamlit as st
from database import save_db
import base64
from datetime import date


# =====================================================
# HR MANAGEMENT UI
# =====================================================

def hr_management_ui(db):
    """
    واجهة إدارة الموظفين بالكامل
    """

    st.subheader("👥 Employee Management")

    users = db["users"]

    # =============================
    # SELECT EMPLOYEE
    # =============================
    target = st.selectbox(
        "Select Employee",
        list(users.keys())
    )

    if not target:
        return

    u = users[target]

    st.divider()

    # =============================
    # EDIT PERSONAL INFO
    # =============================
    st.markdown("### 📝 Edit Personal Info")

    full_name = st.text_input("Full Name", value=u.get("full_name", ""))
    password = st.text_input("Password", value=u.get("pass", ""))
    salary = st.number_input("Salary", value=float(u.get("salary", 0)))

    if st.button("💾 Save Changes"):
        users[target]["full_name"] = full_name
        users[target]["pass"] = password
        users[target]["salary"] = salary

        save_db(db)
        st.success("✅ Updated")

    st.divider()

    # =============================
    # BONUS / DEDUCTION / OVERTIME
    # =============================
    st.markdown("### 💰 Financial Records")

    record_type = st.radio(
        "Type",
        ["Bonus", "Deduction", "Overtime", "Extra Leave"]
    )

    amount = st.number_input("Amount")
    note = st.text_input("Reason")

    if st.button("➕ Add Record"):

        key_map = {
            "Bonus": "bonus",
            "Deduction": "deductions",
            "Overtime": "overtime",
            "Extra Leave": "extra_leaves"
        }

        key = key_map[record_type]

        users[target][key].append({
            "date": str(date.today()),
            "val": amount,
            "note": note
        })

        save_db(db)
        st.success("✅ Added")

    st.divider()

    # =============================
    # DELETE EMPLOYEE
    # =============================
    if target != "admin":
        if st.button("🗑 Delete Employee"):
            del users[target]
            save_db(db)
            st.warning("User Deleted")
            st.rerun()
