# =====================================================
# TRAINING SERVICE
# =====================================================

from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from auth_service import get_current_username
from database import save_db


# =====================================================
# Default training content
# =====================================================
DEFAULT_TRAINING_CONTENT = {
    "Professional Standards": [
        "Arrive 15 minutes early",
        "Proper handover before shift",
        "Biometric logging mandatory",
        "Follow company attendance rules",
    ],
    "Technical Operations": [
        "Check voltage before power-on",
        "Handle paper jam carefully",
        "Monitor printer quality",
        "Use tools safely",
    ],
    "Customer Excellence": [
        "Greet customer professionally",
        "Listen without interruption",
        "Confirm before delivery",
        "Resolve complaints calmly",
    ],
    "Digital Tools": [
        "Use Canva for simple content",
        "Use AI tools responsibly",
        "Use Office tools correctly",
    ],
}


# =====================================================
# Data helpers
# =====================================================
def ensure_training_defaults(db: dict) -> bool:
    changed = False

    if "training_content" not in db or not isinstance(db.get("training_content"), dict):
        db["training_content"] = dict(DEFAULT_TRAINING_CONTENT)
        changed = True

    if "training_progress" not in db or not isinstance(db.get("training_progress"), dict):
        db["training_progress"] = {}
        changed = True

    if "training_records" not in db or not isinstance(db.get("training_records"), dict):
        db["training_records"] = {}
        changed = True

    return changed


def get_training_content(db: dict) -> dict:
    ensure_training_defaults(db)
    return db.get("training_content", {})


def get_training_progress(db: dict, username: str) -> dict:
    ensure_training_defaults(db)
    return db.get("training_progress", {}).get(username, {})


def set_training_progress(db: dict, username: str, progress: dict) -> None:
    ensure_training_defaults(db)
    db.setdefault("training_progress", {})
    db["training_progress"][username] = progress


def get_training_completion_percent(db: dict, username: str) -> float:
    content = get_training_content(db)
    progress = get_training_progress(db, username)

    total_items = 0
    checked_items = 0

    for section_name, items in content.items():
        for item in items:
            total_items += 1
            if progress.get(section_name, {}).get(item, False):
                checked_items += 1

    if total_items == 0:
        return 0.0

    return round((checked_items / total_items) * 100, 2)


def is_training_fully_completed(db: dict, username: str) -> bool:
    content = get_training_content(db)
    progress = get_training_progress(db, username)

    for section_name, items in content.items():
        for item in items:
            if not progress.get(section_name, {}).get(item, False):
                return False

    return True


# =====================================================
# Employee training page
# =====================================================
def render_employee_training_page(db: dict) -> None:
    ensure_training_defaults(db)

    username = get_current_username() or ""
    if not username:
        st.error("No active user found.")
        return

    training_content = get_training_content(db)
    progress = get_training_progress(db, username)

    st.subheader("🎓 Employee Training Center")
    st.caption("أكمل جميع عناصر التدريب ثم اعتمد الإنهاء النهائي.")

    completion_percent = get_training_completion_percent(db, username)
    st.progress(min(max(completion_percent / 100, 0.0), 1.0))
    st.metric("Completion", f"{completion_percent:.0f}%")

    for section_name, items in training_content.items():
        with st.expander(section_name, expanded=True):
            st.markdown(
                f"""
                <div style="
                    padding:12px 14px;
                    border-radius:12px;
                    background:#F8FAFC;
                    border:1px solid #E2E8F0;
                    margin-bottom:12px;
                    font-weight:600;
                ">
                    {section_name}
                </div>
                """,
                unsafe_allow_html=True,
            )

            for idx, item in enumerate(items):
                checked = bool(progress.get(section_name, {}).get(item, False))
                new_checked = st.checkbox(
                    item,
                    value=checked,
                    key=f"training_{username}_{section_name}_{idx}_{item}",
                )

                progress.setdefault(section_name, {})
                progress[section_name][item] = new_checked

    set_training_progress(db, username, progress)
    save_db(db)

    st.divider()

    fully_completed = is_training_fully_completed(db, username)
    agree = st.checkbox(
        "I confirm that I completed all training items and understood the policies.",
        key=f"training_agree_{username}",
    )

    c1, c2 = st.columns([2, 1])

    with c1:
        if not fully_completed:
            st.warning("يجب إكمال كل عناصر التدريب أولًا قبل الاعتماد النهائي.")
        elif username in db.get("training_records", {}):
            st.success("تم اعتماد التدريب لهذا الموظف بالفعل.")
        else:
            st.success("جميع عناصر التدريب مكتملة. يمكنك الاعتماد الآن.")

    with c2:
        if st.button("✅ Confirm Completion", use_container_width=True):
            if not fully_completed:
                st.error("من فضلك أكمل كل عناصر التدريب أولًا.")
            elif not agree:
                st.warning("من فضلك فعّل مربع التأكيد أولًا.")
            else:
                db.setdefault("training_records", {})
                db["training_records"][username] = {
                    "date": str(date.today()),
                    "status": "completed",
                    "completion_percent": 100,
                }
                save_db(db)
                st.success(f"Training Completed ✔ Recorded for {username}")
                st.balloons()
                st.rerun()


# =====================================================
# Admin training manager
# =====================================================
def render_training_admin_manager(db: dict) -> None:
    ensure_training_defaults(db)

    st.subheader("🛠️ Training Content Manager")
    st.caption("إضافة وتعديل وحذف أقسام وبنود التدريب من هنا.")

    training_content = db.get("training_content", {})

    tab_manage, tab_progress = st.tabs(["Manage Content", "Employee Progress"])

    with tab_manage:
        st.markdown("### Training Sections")

        section_names = list(training_content.keys())
        if section_names:
            selected_section = st.selectbox("Select Section", section_names, key="training_admin_section_select")
        else:
            selected_section = None
            st.info("لا يوجد أي قسم تدريب حتى الآن.")

        c1, c2 = st.columns(2)

        with c1:
            new_section_name = st.text_input("New Section Name", key="training_new_section_name")
            if st.button("➕ Add Section", use_container_width=True):
                section_name = new_section_name.strip()
                if not section_name:
                    st.warning("Section name is required.")
                elif section_name in training_content:
                    st.warning("This section already exists.")
                else:
                    training_content[section_name] = []
                    db["training_content"] = training_content
                    save_db(db)
                    st.success("Section added successfully.")
                    st.rerun()

        with c2:
            if selected_section:
                rename_section_name = st.text_input(
                    "Rename Section",
                    value=selected_section,
                    key="training_rename_section_name",
                )
                if st.button("✏️ Rename Section", use_container_width=True):
                    new_name = rename_section_name.strip()
                    if not new_name:
                        st.warning("New section name is required.")
                    elif new_name == selected_section:
                        st.info("No changes detected.")
                    elif new_name in training_content:
                        st.warning("Another section already uses this name.")
                    else:
                        training_content[new_name] = training_content.pop(selected_section)
                        db["training_content"] = training_content
                        save_db(db)
                        st.success("Section renamed successfully.")
                        st.rerun()

        if selected_section:
            st.divider()
            st.markdown(f"### Items in: {selected_section}")

            items = training_content.get(selected_section, [])

            if items:
                for idx, item in enumerate(items):
                    col_item, col_delete = st.columns([6, 1])
                    with col_item:
                        updated_value = st.text_input(
                            f"Item {idx + 1}",
                            value=item,
                            key=f"training_item_edit_{selected_section}_{idx}",
                        )
                    with col_delete:
                        if st.button("🗑️", key=f"training_item_delete_{selected_section}_{idx}"):
                            training_content[selected_section].pop(idx)
                            db["training_content"] = training_content
                            save_db(db)
                            st.success("Item deleted.")
                            st.rerun()

                    if updated_value.strip() != item:
                        training_content[selected_section][idx] = updated_value.strip()

                if st.button("💾 Save Item Edits", use_container_width=True):
                    db["training_content"] = training_content
                    save_db(db)
                    st.success("Items updated successfully.")
                    st.rerun()
            else:
                st.info("No items in this section yet.")

            st.divider()

            new_item = st.text_input("New Training Item", key=f"training_new_item_{selected_section}")
            if st.button("➕ Add Item", use_container_width=True):
                item_value = new_item.strip()
                if not item_value:
                    st.warning("Training item is required.")
                else:
                    training_content[selected_section].append(item_value)
                    db["training_content"] = training_content
                    save_db(db)
                    st.success("Item added successfully.")
                    st.rerun()

            if st.button("🗑️ Delete Entire Section", type="primary", use_container_width=True):
                training_content.pop(selected_section, None)
                db["training_content"] = training_content
                save_db(db)
                st.success("Section deleted successfully.")
                st.rerun()

    with tab_progress:
        st.markdown("### Employee Training Progress")

        users = db.get("users", {})
        training_records = db.get("training_records", {})

        if not users:
            st.info("No users found.")
            return

        rows = []
        for username, user_info in users.items():
            percent = get_training_completion_percent(db, username)
            record = training_records.get(username, {})
            rows.append(
                {
                    "Username": username,
                    "Full Name": user_info.get("full_name", username),
                    "Role": user_info.get("role", "-"),
                    "Completion %": percent,
                    "Status": record.get("status", "pending"),
                    "Completed Date": record.get("date", "-"),
                }
            )

        st.dataframe(
            rows,
            use_container_width=True,
            column_config={
                "Completion %": st.column_config.NumberColumn(format="%.0f"),
            },
        )


# =====================================================
# Main public renderer
# =====================================================
def render_training_module(db: dict, admin_mode: bool = False) -> None:
    ensure_training_defaults(db)

    if admin_mode:
        render_training_admin_manager(db)
    else:
        render_employee_training_page(db)
