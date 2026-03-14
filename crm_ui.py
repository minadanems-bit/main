# =====================================================
# CRM UI
# Tasks, messages, notifications, and team follow-up
# =====================================================

import pandas as pd
import streamlit as st

from auth_service import get_current_username
from database import load_db
from crm_service import (
    DEFAULT_CRM_PRIORITIES,
    DEFAULT_CRM_TASK_STATUSES,
    add_crm_task_comment,
    create_crm_task,
    get_all_users,
    get_crm_dashboard_stats,
    get_crm_task_by_id,
    get_crm_tasks,
    get_inbox_messages,
    get_sent_messages,
    get_user_full_name,
    get_user_notifications,
    mark_all_notifications_as_read,
    mark_message_as_read,
    mark_notification_as_read,
    reassign_crm_task,
    send_internal_message,
    update_crm_task_status,
)


# =====================================================
# Helpers
# =====================================================
def _safe_text(value, default="-"):
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _priority_label(value: str) -> str:
    labels = {
        "low": "Low",
        "normal": "Normal",
        "high": "High",
        "urgent": "Urgent",
    }
    return labels.get(str(value).strip().lower(), str(value).title())


def _status_label(value: str) -> str:
    return DEFAULT_CRM_TASK_STATUSES.get(str(value).strip().lower(), str(value).replace("_", " ").title())


def _user_display(db: dict, username: str) -> str:
    return f"{get_user_full_name(db, username)} ({username})"


def _task_options_label(db: dict, task: dict) -> str:
    return f"{task.get('title', '-') } | {_status_label(task.get('status', 'new'))} | {_safe_text(task.get('assigned_to'))}"


# =====================================================
# Dashboard
# =====================================================
def render_crm_dashboard(db: dict, current_user: str) -> None:
    stats = get_crm_dashboard_stats(db, current_user)

    st.subheader("📊 CRM Dashboard")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("My Tasks", stats.get("my_tasks_total", 0))
    with c2:
        st.metric("Unread Messages", stats.get("my_unread_messages", 0))
    with c3:
        st.metric("Unread Notifications", stats.get("my_unread_notifications", 0))

    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("New Tasks", stats.get("my_tasks_new", 0))
    with c5:
        st.metric("In Progress", stats.get("my_tasks_in_progress", 0))
    with c6:
        st.metric("Waiting", stats.get("my_tasks_waiting", 0))


# =====================================================
# Create Task
# =====================================================
def render_create_task_tab(db: dict, current_user: str) -> None:
    st.subheader("➕ Create CRM Task")

    users = get_all_users(db)
    if not users:
        st.warning("No users found.")
        return

    assign_to = st.selectbox(
        "Assign To",
        users,
        format_func=lambda x: _user_display(db, x),
        key="crm_assign_to",
    )

    title = st.text_input("Task Title", key="crm_task_title")
    description = st.text_area("Task Description", key="crm_task_description")
    priority = st.selectbox("Priority", DEFAULT_CRM_PRIORITIES, index=1, key="crm_task_priority")
    due_date = st.text_input("Due Date", placeholder="YYYY-MM-DD", key="crm_task_due_date")

    branches = db.get("branches", []) or [""]
    branch = st.selectbox("Branch", branches, key="crm_task_branch")

    related_category = st.text_input(
        "Related Category",
        placeholder="opening / closing / hr / design / moderation ...",
        key="crm_related_category",
    )

    if st.button("✅ Create Task", use_container_width=True):
        success, message = create_crm_task(
            created_by=current_user,
            assigned_to=assign_to,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            branch=branch,
            related_category=related_category,
        )
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


# =====================================================
# My Tasks
# =====================================================
def render_my_tasks_tab(db: dict, current_user: str) -> None:
    st.subheader("📌 My Tasks")

    my_tasks = get_crm_tasks(db, assigned_to=current_user)

    if not my_tasks:
        st.info("No tasks assigned to you.")
        return

    task_map = {task["id"]: task for task in my_tasks}
    selected_task_id = st.selectbox(
        "Select Task",
        list(task_map.keys()),
        format_func=lambda x: _task_options_label(db, task_map[x]),
        key="crm_my_task_selector",
    )

    task = task_map[selected_task_id]

    st.markdown(f"### {_safe_text(task.get('title'))}")
    st.write(f"**Assigned To:** {_safe_text(task.get('assigned_to'))}")
    st.write(f"**Created By:** {_safe_text(task.get('created_by'))}")
    st.write(f"**Priority:** {_priority_label(task.get('priority', 'normal'))}")
    st.write(f"**Status:** {_status_label(task.get('status', 'new'))}")
    st.write(f"**Due Date:** {_safe_text(task.get('due_date'))}")
    st.write(f"**Branch:** {_safe_text(task.get('branch'))}")
    st.write(f"**Related Category:** {_safe_text(task.get('related_category'))}")

    st.divider()
    st.write("**Description**")
    st.info(_safe_text(task.get("description"), "No description"))

    st.divider()
    st.write("**Update Status**")

    new_status = st.selectbox(
        "New Status",
        list(DEFAULT_CRM_TASK_STATUSES.keys()),
        index=list(DEFAULT_CRM_TASK_STATUSES.keys()).index(task.get("status", "new"))
        if task.get("status", "new") in DEFAULT_CRM_TASK_STATUSES
        else 0,
        format_func=_status_label,
        key=f"crm_status_{selected_task_id}",
    )
    status_note = st.text_input("Status Note", key=f"crm_status_note_{selected_task_id}")

    if st.button("🔄 Update Task Status", use_container_width=True, key=f"crm_update_status_btn_{selected_task_id}"):
        success, message = update_crm_task_status(
            task_id=selected_task_id,
            new_status=new_status,
            changed_by=current_user,
            note=status_note,
        )
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.divider()
    st.write("**Comments**")

    comments = task.get("comments", [])
    if comments:
        for item in comments:
            st.markdown(
                f"""
                <div style="padding:10px;border:1px solid #ddd;border-radius:10px;margin-bottom:8px;">
                <b>{_safe_text(item.get('comment_by'))}</b><br>
                {_safe_text(item.get('comment_text'))}<br>
                <small>{_safe_text(item.get('created_at'))}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No comments yet.")

    new_comment = st.text_area("Add Comment", key=f"crm_comment_{selected_task_id}")
    if st.button("💬 Add Comment", use_container_width=True, key=f"crm_comment_btn_{selected_task_id}"):
        success, message = add_crm_task_comment(
            task_id=selected_task_id,
            comment_by=current_user,
            comment_text=new_comment,
        )
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


# =====================================================
# Team Tasks
# =====================================================
def render_team_tasks_tab(db: dict, current_user: str) -> None:
    st.subheader("👥 Team Tasks")

    tasks = get_crm_tasks(db)
    if not tasks:
        st.info("No CRM tasks found.")
        return

    df = pd.DataFrame(
        [
            {
                "Title": item.get("title", "-"),
                "Assigned To": item.get("assigned_to", "-"),
                "Created By": item.get("created_by", "-"),
                "Priority": _priority_label(item.get("priority", "normal")),
                "Status": _status_label(item.get("status", "new")),
                "Due Date": item.get("due_date", "-"),
                "Branch": item.get("branch", "-"),
            }
            for item in tasks
        ]
    )
    st.dataframe(df, use_container_width=True)

    task_map = {task["id"]: task for task in tasks}
    selected_task_id = st.selectbox(
        "Select Task To Reassign",
        list(task_map.keys()),
        format_func=lambda x: _task_options_label(db, task_map[x]),
        key="crm_team_task_selector",
    )

    users = get_all_users(db)
    new_assignee = st.selectbox(
        "Reassign To",
        users,
        format_func=lambda x: _user_display(db, x),
        key="crm_new_assignee",
    )
    reassign_note = st.text_input("Reassign Note", key="crm_reassign_note")

    if st.button("🔁 Reassign Task", use_container_width=True):
        success, message = reassign_crm_task(
            task_id=selected_task_id,
            new_assignee=new_assignee,
            changed_by=current_user,
            note=reassign_note,
        )
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


# =====================================================
# Messages
# =====================================================
def render_messages_tab(db: dict, current_user: str) -> None:
    st.subheader("✉️ Internal Messages")

    users = [u for u in get_all_users(db) if u != current_user]

    with st.expander("Send New Message", expanded=False):
        if users:
            receiver = st.selectbox(
                "To",
                users,
                format_func=lambda x: _user_display(db, x),
                key="crm_msg_receiver",
            )
            subject = st.text_input("Subject", key="crm_msg_subject")
            body = st.text_area("Message", key="crm_msg_body")

            if st.button("📨 Send Message", use_container_width=True):
                success, message = send_internal_message(
                    sender_username=current_user,
                    receiver_username=receiver,
                    subject=subject,
                    message_text=body,
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.info("No available users to message.")

    inbox = get_inbox_messages(db, current_user)
    sent = get_sent_messages(db, current_user)

    tab1, tab2 = st.tabs(["Inbox", "Sent"])

    with tab1:
        if inbox:
            for item in inbox:
                st.markdown(
                    f"""
                    <div style="padding:12px;border:1px solid #ddd;border-radius:10px;margin-bottom:10px;">
                    <b>From:</b> {_safe_text(item.get('sender_username'))}<br>
                    <b>Subject:</b> {_safe_text(item.get('subject'))}<br>
                    <b>Message:</b><br>{_safe_text(item.get('message_text'))}<br>
                    <small>{_safe_text(item.get('created_at'))}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if not bool(item.get("is_read", False)):
                    if st.button("✅ Mark As Read", key=f"read_msg_{item.get('id')}"):
                        success, message = mark_message_as_read(item.get("id"))
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("Inbox is empty.")

    with tab2:
        if sent:
            for item in sent:
                st.markdown(
                    f"""
                    <div style="padding:12px;border:1px solid #ddd;border-radius:10px;margin-bottom:10px;">
                    <b>To:</b> {_safe_text(item.get('receiver_username'))}<br>
                    <b>Subject:</b> {_safe_text(item.get('subject'))}<br>
                    <b>Message:</b><br>{_safe_text(item.get('message_text'))}<br>
                    <small>{_safe_text(item.get('created_at'))}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No sent messages yet.")


# =====================================================
# Notifications
# =====================================================
def render_notifications_tab(db: dict, current_user: str) -> None:
    st.subheader("🔔 Notifications")

    notifications = get_user_notifications(db, current_user, unread_only=False)

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("✅ Mark All Read", use_container_width=True):
            success, message = mark_all_notifications_as_read(current_user)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with c2:
        unread_count = len([n for n in notifications if not bool(n.get("is_read", False))])
        st.info(f"Unread Notifications: {unread_count}")

    if notifications:
        for item in notifications:
            is_read = bool(item.get("is_read", False))
            read_label = "Read" if is_read else "Unread"

            st.markdown(
                f"""
                <div style="padding:12px;border:1px solid #ddd;border-radius:10px;margin-bottom:10px;">
                <b>{_safe_text(item.get('title'))}</b><br>
                {_safe_text(item.get('message'))}<br>
                <small>{_safe_text(item.get('created_at'))} | {read_label}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not is_read:
                if st.button("Mark Read", key=f"notif_read_{item.get('id')}"):
                    success, message = mark_notification_as_read(item.get("id"))
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("No notifications found.")


# =====================================================
# Main CRM UI
# =====================================================
def crm_ui() -> None:
    db = load_db()
    current_user = get_current_username()

    if not current_user:
        st.warning("Please login first.")
        return

    st.title("📇 CRM & Internal Communication")
    st.caption("Tasks, coordination, messages, notifications, and follow-up.")

    render_crm_dashboard(db, current_user)

    st.divider()

    tabs = st.tabs(
        [
            "Create Task",
            "My Tasks",
            "Team Tasks",
            "Messages",
            "Notifications",
        ]
    )

    with tabs[0]:
        render_create_task_tab(db, current_user)

    with tabs[1]:
        render_my_tasks_tab(db, current_user)

    with tabs[2]:
        render_team_tasks_tab(db, current_user)

    with tabs[3]:
        render_messages_tab(db, current_user)

    with tabs[4]:
        render_notifications_tab(db, current_user)
