import os
import json
import base64
from datetime import datetime, date

import pandas as pd
import streamlit as st

from database import load_db, save_db
from operations_service import daily_operations_ui
from printer_service import printer_management_ui


# =========================
# Database bootstrap
# =========================
db = load_db()


# =========================
# Helpers
# =========================
def ensure_db_defaults() -> None:
    """Ensure required top-level keys exist in db."""
    defaults = {
        "users": {},
        "logs": [],
        "drafts": {},
        "tasks": {
            "opening": [],
            "closing": [],
            "social": [],
            "interaction": [],
        },
        "branches": [],
        "expense_categories": [],
        "history": [],
        "training_records": {},
    }

    changed = False
    for key, default_value in defaults.items():
        if key not in db:
            db[key] = default_value
            changed = True

    if changed:
        save_db(db)


def get_current_user() -> dict:
    username = st.session_state.get("user")
    if not username:
        return {}
    return db.get("users", {}).get(username, {})


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def log_action(action: str) -> None:
    username = st.session_state.get("user", "unknown")
    db.setdefault("logs", []).append(
        {
            "user": username,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
        }
    )
    save_db(db)


def safe_user_image(user_info: dict, width: int = 120) -> None:
    photo = user_info.get("photo")
    if not photo:
        st.write("👤 No Photo")
        return

    try:
        st.image(base64.b64decode(photo), width=width)
    except Exception:
        st.write("👤 Invalid Photo")


def parse_hiring_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return date(2024, 1, 1)


def sync_draft() -> None:
    """Persist selected session-state draft keys for the logged-in user."""
    if not st.session_state.get("logged_in"):
        return

    user = st.session_state.get("user")
    if not user:
        return

    draft_prefixes = (
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

    draft_data = {
        key: value
        for key, value in st.session_state.items()
        if key.startswith(draft_prefixes)
    }

    db.setdefault("drafts", {})
    db["drafts"][user] = draft_data
    save_db(db)


def restore_user_drafts(username: str) -> None:
    drafts = db.get("drafts", {}).get(username, {})
    for key, value in drafts.items():
        st.session_state[key] = value


def logout() -> None:
    sync_draft()
    st.session_state["logged_in"] = False
    st.session_state.pop("user", None)
    st.session_state.pop("role", None)
    st.rerun()


# =========================
# Auth UI
# =========================
def render_login_screen() -> None:
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
            user_record = db.get("users", {}).get(username, {})

            if (
                username in db.get("users", {})
                and "pass" in user_record
                and user_record.get("pass") == password
            ):
                st.session_state["logged_in"] = True
                st.session_state["user"] = username
                st.session_state["role"] = user_record.get("role", "user")

                restore_user_drafts(username)
                log_action("Login")
                st.rerun()
            else:
                st.error("❌ Access Denied")

    st.stop()


# =========================
# Employee self service
# =========================
def render_self_service(user_info: dict) -> None:
    st.divider()
    st.subheader("📂 My Financial Profile")
    st.write(f"**📅 Hiring Date:** {user_info.get('hiring_date', '-')}")

    salary = float(user_info.get("salary", 0) or 0)
    st.metric("💰 Base Salary", f"{salary:,.2f} LE")

    with st.expander("🎁 My Bonuses", expanded=False):
        if user_info.get("bonus"):
            st.dataframe(pd.DataFrame(user_info["bonus"]), use_container_width=True)
        else:
            st.info("No bonuses yet.")

    with st.expander("⏳ Overtime", expanded=False):
        if user_info.get("overtime"):
            st.dataframe(pd.DataFrame(user_info["overtime"]), use_container_width=True)
        else:
            st.info("No overtime yet.")

    with st.expander("⚠️ My Deductions", expanded=False):
        if user_info.get("deductions"):
            st.dataframe(pd.DataFrame(user_info["deductions"]), use_container_width=True)
        else:
            st.success("Clean Record! No deductions.")

    with st.expander("🏖️ Extra Leave", expanded=False):
        if user_info.get("extra_leaves"):
            st.dataframe(pd.DataFrame(user_info["extra_leaves"]), use_container_width=True)
        else:
            st.success("Clean Record! No extra leaves.")


# =========================
# Admin modules
# =========================
def render_hr_module() -> None:
    from hr_service import hr_management_ui

    hr_management_ui(db)


def render_payroll_module() -> None:
    st.info("Manage Salaries, Bonuses & Deductions")

    users = list(db.get("users", {}).keys())
    if not users:
        st.warning("No employees found.")
        return

    target = st.selectbox("Select Employee", users)
    user_fin = db["users"].get(target, {})

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        salary = st.number_input(
            "Base Salary",
            min_value=0.0,
            value=float(user_fin.get("salary", 0) or 0),
            step=100.0,
        )
    with col_s2:
        hiring_date = st.date_input(
            "Hiring Date",
            value=parse_hiring_date(user_fin.get("hiring_date", "2024-01-01")),
        )

    if st.button("💾 Update Contract"):
        db["users"][target]["salary"] = salary
        db["users"][target]["hiring_date"] = str(hiring_date)
        save_db(db)
        st.success("Contract Updated")

    st.divider()
    st.write("**Add Financial Entry:**")

    entry_type = st.radio(
        "Type",
        ["Bonus 🎁", "Deductions ⚠️", "Overtime ⏳", "Extra Leave 🏖️"],
        horizontal=True,
    )
    amount = st.number_input("Value (LE)", min_value=0.0, step=10.0)
    note = st.text_input("Reason / Note")

    if st.button("✅ Submit Entry"):
        key_map = {
            "Bonus 🎁": "bonus",
            "Deductions ⚠️": "deductions",
            "Overtime ⏳": "overtime",
            "Extra Leave 🏖️": "extra_leaves",
        }
        target_key = key_map[entry_type]

        db["users"][target].setdefault(target_key, [])
        db["users"][target][target_key].append(
            {
                "date": str(date.today()),
                "amount": amount,
                "note": note,
            }
        )
        save_db(db)
        st.success("Added to HR Record")


def render_tasks_module() -> None:
    st.info("Manage operational tasks and checklists")

    category = st.selectbox("Category", ["opening", "closing", "social", "interaction"])
    db.setdefault("tasks", {})
    db["tasks"].setdefault(category, [])

    for index, task in enumerate(db["tasks"][category]):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.text(f"📌 {task}")
        with c2:
            if st.button("🗑️", key=f"del_t_{category}_{index}"):
                db["tasks"][category].pop(index)
                save_db(db)
                st.rerun()

    new_task = st.text_input("New Task")
    if st.button("➕ Add Task"):
        if new_task.strip():
            db["tasks"][category].append(new_task.strip())
            save_db(db)
            st.rerun()


def render_branches_expenses_module() -> None:
    st.info("Manage Locations & Expenses")

    st.write("**🏢 Branches (الفروع)**")
    branches = db.setdefault("branches", [])

    if branches:
        branch_selected = st.selectbox("Select Branch", branches)
        c_br1, c_br2 = st.columns(2)

        with c_br1:
            new_branch_name = st.text_input("Rename Branch", value=branch_selected)
            if st.button("✏️ Rename"):
                if new_branch_name.strip():
                    idx = branches.index(branch_selected)
                    branches[idx] = new_branch_name.strip()
                    save_db(db)
                    st.success("Renamed!")
                    st.rerun()

        with c_br2:
            if st.button("🗑️ Delete Branch", type="primary"):
                branches.remove(branch_selected)
                save_db(db)
                st.warning("Deleted!")
                st.rerun()
    else:
        st.info("No branches yet.")

    new_branch = st.text_input("New Branch Name")
    if st.button("➕ Create Branch"):
        if new_branch.strip():
            branches.append(new_branch.strip())
            save_db(db)
            st.rerun()

    st.divider()
    st.write("**💸 Expense Categories (بنود المصاريف)**")

    db.setdefault("expense_categories", [])
    for index, expense in enumerate(db["expense_categories"]):
        ce1, ce2 = st.columns([5, 1])
        with ce1:
            st.text(f"🔹 {expense}")
        with ce2:
            if st.button("✖️", key=f"del_ex_{index}"):
                db["expense_categories"].pop(index)
                save_db(db)
                st.rerun()

    new_expense = st.text_input("New Expense Category")
    if st.button("➕ Add Expense Category"):
        if new_expense.strip():
            db["expense_categories"].append(new_expense.strip())
            save_db(db)
            st.rerun()


def render_archive_history_module() -> None:
    st.header("📂 Archive & History")

    if not is_admin():
        st.error("Access Denied: Admins Only.")
        return

    st.divider()

    history = db.get("history", [])
    if not history:
        st.info("No archived shifts found yet.")
        return

    try:
        total_sales = sum(float(item.get("sales", 0) or 0) for item in history)
        total_expenses = sum(float(item.get("expenses", 0) or 0) for item in history)
        total_diff = sum(float(item.get("diff", 0) or 0) for item in history)
    except ValueError:
        st.error("Error in data types within History. Please check database.")
        total_sales = total_expenses = total_diff = 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Sales", f"{total_sales:,.2f} LE")
    m2.metric("Total Expenses", f"{total_expenses:,.2f} LE")
    m3.metric("Net Cash Diff", f"{total_diff:,.2f} LE", delta=total_diff, delta_color="normal")

    st.divider()
    st.subheader("📜 Detailed Shift History")

    df_history = pd.DataFrame(reversed(history))

    column_mapping = {
        "date": "Date",
        "staff": "Employee",
        "branch": "Branch",
        "sales": "Sales",
        "expenses": "Expenses",
        "exp_note": "Exp. Details",
        "diff": "Cash Diff",
        "kyo_jam": "Kyo Jam",
        "xerox_jam": "Xerox Jam",
    }

    existing_columns = {
        old_name: new_name
        for old_name, new_name in column_mapping.items()
        if old_name in df_history.columns
    }

    st.dataframe(
        df_history.rename(columns=existing_columns),
        use_container_width=True,
        column_config={
            "Sales": st.column_config.NumberColumn(format="%.2f LE"),
            "Expenses": st.column_config.NumberColumn(format="%.2f LE"),
            "Cash Diff": st.column_config.NumberColumn(format="%.2f LE"),
        },
    )

    st.divider()
    with st.expander("🗑️ Advanced Settings (Danger Zone)"):
        st.warning("Action below is irreversible!")
        confirm_check = st.checkbox("I understand that 'Clear History' will delete everything.")
        if confirm_check and st.button("🚨 Permanently Clear All History"):
            db["history"] = []
            save_db(db)
            st.success("History Cleared!")
            st.rerun()


def render_training_module() -> None:
    st.markdown(
        """
        <style>
        .training-title {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            color: #0F172A;
            margin-bottom: 20px;
        }

        .training-card {
            padding: 20px;
            border-radius: 15px;
            background: #F8FAFC;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }

        .section-header {
            font-size: 20px;
            font-weight: bold;
            color: #1E3A8A;
            border-left: 6px solid #1E3A8A;
            padding-left: 10px;
            margin-bottom: 10px;
        }

        .highlight-box {
            padding: 15px;
            background: #EFF6FF;
            border-radius: 10px;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("🚀")
    st.markdown(
        "<div class='training-title'>NMS Enterprise | Professional Training Center</div>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "📜 Professional Standards",
            "⚙ Technical Operations",
            "🤝 Customer Excellence",
            "💻 Digital Transformation",
        ]
    )

    with tabs[0]:
        st.markdown("<div class='training-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🎯 Workplace Commitment</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                🔵 **Attendance**
                - Arrive 15 minutes early
                - Proper handover before shift
                - Biometric logging mandatory
                """
            )

        with col2:
            st.markdown(
                """
                🔵 **Financial Responsibility**
                - No printing without system record
                - 50% minimum deposit policy
                - Employee responsible for cash shortage
                """
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown("<div class='training-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🖨 Equipment Handling</div>", unsafe_allow_html=True)

        with st.expander("📠 Printer Operation"):
            st.markdown(
                """
                ✅ Check voltage before power-on  
                ✅ Clear paper jam carefully  
                ✅ Monitor print quality every 100 pages  
                """
            )

        with st.expander("✂ Finishing Equipment"):
            st.markdown(
                """
                ✅ Thermal binding – wait for green light  
                ✅ Paper cutting – follow safety rules  
                ✅ Spiral binding – choose correct size  
                """
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown("<div class='training-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🌟 Service Excellence Model</div>", unsafe_allow_html=True)

        st.markdown(
            """
            🟢 Greet with professionalism  
            🟢 Listen without interruption  
            🟢 Confirm before final delivery  
            🟢 Resolve complaints calmly  
            """
        )

        st.markdown(
            "<div class='highlight-box'>💡 Remember: Customer trust = Business growth</div>",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown("<div class='training-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🚀 Modern Tools</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.image("https://img.icons8.com/color/96/canva.png", width=60)
            st.markdown("**Canva**\nDesign & Social Media Content")

        with c2:
            st.image("https://img.icons8.com/color/96/chatgpt.png", width=60)
            st.markdown("**AI Tools**\nSmart Automation & Text Optimization")

        with c3:
            st.image("https://img.icons8.com/color/96/microsoft-excel-2019.png", width=60)
            st.markdown("**Office Tools**\nData & Reporting Mastery")

        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📝 Training Acknowledgement")

    agree = st.checkbox("I confirm that I have completed the training and understood all policies.")

    if st.button("✅ Confirm Completion", use_container_width=True):
        if agree:
            db.setdefault("training_records", {})
            db["training_records"][st.session_state.get("user")] = {
                "date": str(date.today()),
                "status": "completed",
            }
            save_db(db)
            st.success(f"Training Completed ✔ Recorded for {st.session_state.get('user')}")
            st.balloons()
        else:
            st.warning("Please confirm the checkbox first.")


def render_printer_management_module() -> None:
    printer_management_ui(db)


def render_admin_panel() -> None:
    st.divider()
    st.subheader("⚙️ Admin Authority")

    admin_choice = st.selectbox(
        "Select Management Module:",
        [
            "👥 Manage Employees (HR)",
            "💰 Payroll & Money",
            "📝 Tasks & Checklists",
            "🏢 Branches & Expenses",
            "🖨 Printer Management",
            "📂 Archive & History",
            "🎓 Employee Training",
        ],
    )

    if admin_choice == "👥 Manage Employees (HR)":
        render_hr_module()
    elif admin_choice == "💰 Payroll & Money":
        render_payroll_module()
    elif admin_choice == "📝 Tasks & Checklists":
        render_tasks_module()
    elif admin_choice == "🏢 Branches & Expenses":
        render_branches_expenses_module()
    elif admin_choice == "🖨 Printer Management":
        render_printer_management_module()
    elif admin_choice == "📂 Archive & History":
        render_archive_history_module()
    elif admin_choice == "🎓 Employee Training":
        render_training_module()


# =========================
# Sidebar
# =========================
def render_sidebar() -> None:
    with st.sidebar:
        user_info = get_current_user()

        safe_user_image(user_info)
        st.header(f"Hi, {user_info.get('full_name', st.session_state.get('user', 'User'))}")

        if st.session_state.get("role") == "user":
            render_self_service(user_info)

        if st.button("🚪 Logout", use_container_width=True):
            logout()

        if is_admin():
            render_admin_panel()


# =========================
# Backup manager
# =========================
def render_backup_manager() -> None:
    if not is_admin():
        return

    backup_folder = "backups"
    os.makedirs(backup_folder, exist_ok=True)

    with st.expander("🧰 Backup Manager"):
        backup_files = sorted(os.listdir(backup_folder), reverse=True)

        if not backup_files:
            st.warning("لا توجد نسخ احتياطية حتى الآن.")
        else:
            latest_file = backup_files[0]
            latest_path = os.path.join(backup_folder, latest_file)

            st.info(f"🕒 أحدث نسخة: {latest_file}")

            with open(latest_path, "rb") as f:
                st.download_button(
                    "📥 تحميل النسخة الاحتياطية",
                    f,
                    file_name=latest_file,
                )

    st.markdown("### ♻️ استرجاع نسخة قديمة")

    backup_files = sorted(os.listdir(backup_folder), reverse=True)
    if not backup_files:
        st.info("لا توجد ملفات نسخ احتياطية للاسترجاع.")
        return

    restore_file = st.selectbox("اختر نسخة احتياطية", backup_files)

    if st.button("♻️ استرجاع النسخة المحددة"):
        selected_path = os.path.join(backup_folder, restore_file)
        with open(selected_path, "r", encoding="utf-8") as f:
            restored_data = json.load(f)

        db.clear()
        db.update(restored_data)
        save_db(db)
        st.success("✅ تم استرجاع النسخة بنجاح")
        st.rerun()


# =========================
# Main app
# =========================
def main() -> None:
    ensure_db_defaults()

    if not st.session_state.get("logged_in", False):
        render_login_screen()

    render_sidebar()
    render_backup_manager()

    if st.session_state.get("logged_in"):
        daily_operations_ui(db)


if __name__ == "__main__":
    main()
