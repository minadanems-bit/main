# =====================================================
# DASHBOARD SERVICE
# Dashboard page rendering
# =====================================================

from __future__ import annotations

import streamlit as st

from constants import ROLE_CLEANER, ROLE_EMPLOYEE
from role_service import can_access_daily_operations, get_daily_operations_block_message
from ui_helpers import render_attendance_clock_widget, render_role_dashboard_cards


def render_dashboard_page(
    *,
    db: dict,
    user_info: dict,
    username: str,
    current_role: str,
    normalized_role: str,
    training_info: dict | None,
    get_role_label,
    set_main_view,
    nav_profile: str,
    nav_operations: str,
    nav_admin: str,
    nav_backup: str,
    can_open_admin_panel,
    can_open_backup_manager,
) -> None:
    st.title("🏠 Dashboard")
    st.caption("واجهة رئيسية أوضح وأذكى حسب دور المستخدم.")

    render_attendance_clock_widget()

    top1, top2, top3 = st.columns(3)
    with top1:
        st.metric("User", username)
    with top2:
        st.metric("Role", get_role_label(current_role))
    with top3:
        st.metric("Training", (training_info or {}).get("status", "pending"))

    st.divider()

    render_role_dashboard_cards(
        normalized_role=normalized_role,
        user_info=user_info,
        db=db,
        training_info=training_info,
    )

    st.divider()

    st.subheader("Quick Access")

    quick_buttons = [
        ("👤 Open My Profile", nav_profile),
        ("📊 Open Daily Operations", nav_operations),
    ]

    if can_open_admin_panel():
        quick_buttons.append(("⚙️ Open Admin Panel", nav_admin))

    if can_open_backup_manager():
        quick_buttons.append(("🧰 Open Backup Manager", nav_backup))

    cols = st.columns(len(quick_buttons))
    for idx, (label, target_view) in enumerate(quick_buttons):
        with cols[idx]:
            if st.button(label, use_container_width=True, key=f"quick_btn_{idx}"):
                set_main_view(target_view)
                st.rerun()

    st.divider()

    st.subheader("Summary")
    st.write(f"**Full Name:** {user_info.get('full_name', '-')}")
    st.write(f"**Job Title:** {user_info.get('job_title', '-')}")
    st.write(f"**Employee Code:** {user_info.get('employee_code', '-') or '-'}")

    if normalized_role == ROLE_EMPLOYEE:
        st.info("يمكنك استخدام الأقسام المخصصة لك فقط حسب صلاحياتك.")
    elif normalized_role == ROLE_CLEANER:
        st.info("يمكنك استخدام أقسام النظافة والتقرير حسب صلاحياتك.")
    elif not can_access_daily_operations():
        st.warning(get_daily_operations_block_message())
