# =====================================================
# CRM SERVICE
# Internal tasks, messages, notifications, and CRM UI
# =====================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from auth_service import get_current_role, get_current_username
from database import load_db, save_db


# =====================================================
# Defaults
# =====================================================
DEFAULT_CRM_TASK_STATUSES = {
    "new": "New",
    "in_progress": "In Progress",
    "waiting": "Waiting",
    "done": "Done",
    "cancelled": "Cancelled",
}

DEFAULT_CRM_PRIORITIES = ["low", "normal", "high", "urgent"]


# =====================================================
# Helpers
# =====================================================
def _normalize(value: str | None) -> str:
    return str(value or "").strip().lower()


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _generate_id(prefix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}_{stamp}"


def ensure_crm_defaults(db: dict) -> bool:
    changed = False

    if "crm_records" not in db or not isinstance(db.get("crm_records"), list):
        db["crm_records"] = []
        changed = True

    if "crm_notifications" not in db or not isinstance(db.get("crm_notifications"), list):
        db["crm_notifications"] = []
        changed = True

    if "internal_messages" not in db or not isinstance(db.get("internal_messages"), list):
        db["internal_messages"] = []
        changed = True

    return changed


def persist_db(db: dict) -> None:
    save_db(db)


def get_role_label(db: dict, username: str) -> str:
    user = (db.get("users") or {}).get(username, {})
    role_value = _safe_text(user.get("role"), "employee")
    return role_value.replace("_", " ").title()


# =====================================================
# User helpers
# =====================================================
def get_all_users(db: dict) -> list[str]:
    ensure_crm_defaults(db)
    return sorted(list((db.get("users") or {}).keys()))


def get_user_role(db: dict, username: str) -> str:
    return _normalize((db.get("users") or {}).get(username, {}).get("role"))


def get_user_full_name(db: dict, username: str) -> str:
    user = (db.get("users") or {}).get(username, {})
    return _safe_text(user.get("full_name"), username)


def get_user_display_name(db: dict, username: str) -> str:
    full_name = get_user_full_name(db, username)
    return f"{full_name} ({username})"


# =====================================================
# Notifications
# =====================================================
def add_notification(
    db: dict,
    username: str,
    title: str,
    message: str,
    related_type: str = "",
    related_id: str = "",
) -> None:
    ensure_crm_defaults(db)

    db["crm_notifications"].append(
        {
            "id": _generate_id("notif"),
            "username": _safe_text(username),
            "title": _safe_text(title),
            "message": _safe_text(message),
            "related_type": _safe_text(related_type),
            "related_id": _safe_text(related_id),
            "is_read": False,
            "created_at": _now_str(),
        }
    )


def get_user_notifications(db: dict, username: str, unread_only: bool = False) -> list[dict]:
    ensure_crm_defaults(db)
    username = _safe_text(username)

    rows = [
        item for item in db["crm_notifications"]
        if _safe_text(item.get("username")) == username
    ]

    if unread_only:
        rows = [item for item in rows if not bool(item.get("is_read", False))]

    rows.sort(key=lambda x: _safe_text(x.get("created_at")), reverse=True)
    return rows


def mark_notification_as_read(notification_id: str) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    for item in db["crm_notifications"]:
        if _safe_text(item.get("id")) == _safe_text(notification_id):
            item["is_read"] = True
            persist_db(db)
            return True, "Notification marked as read."

    return False, "Notification not found."


def mark_all_notifications_as_read(username: str) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    username = _safe_text(username)
    changed = False

    for item in db["crm_notifications"]:
        if _safe_text(item.get("username")) == username and not bool(item.get("is_read", False)):
            item["is_read"] = True
            changed = True

    if changed:
        persist_db(db)

    return True, "Notifications updated."


# =====================================================
# Internal Messages
# =====================================================
def send_internal_message(
    sender_username: str,
    receiver_username: str,
    subject: str,
    message_text: str,
) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    sender_username = _safe_text(sender_username)
    receiver_username = _safe_text(receiver_username)
    subject = _safe_text(subject)
    message_text = _safe_text(message_text)

    if not sender_username:
        return False, "Sender is required."

    if not receiver_username:
        return False, "Receiver is required."

    if receiver_username not in (db.get("users") or {}):
        return False, "Receiver not found."

    if not subject:
        return False, "Subject is required."

    if not message_text:
        return False, "Message body is required."

    message_id = _generate_id("msg")

    db["internal_messages"].append(
        {
            "id": message_id,
            "sender_username": sender_username,
            "receiver_username": receiver_username,
            "subject": subject,
            "message_text": message_text,
            "is_read": False,
            "created_at": _now_str(),
        }
    )

    add_notification(
        db=db,
        username=receiver_username,
        title="New Internal Message",
        message=f"{sender_username} sent you a message: {subject}",
        related_type="message",
        related_id=message_id,
    )

    persist_db(db)
    return True, "Message sent successfully."


def get_inbox_messages(db: dict, username: str) -> list[dict]:
    ensure_crm_defaults(db)
    username = _safe_text(username)

    rows = [
        item for item in db["internal_messages"]
        if _safe_text(item.get("receiver_username")) == username
    ]
    rows.sort(key=lambda x: _safe_text(x.get("created_at")), reverse=True)
    return rows


def get_sent_messages(db: dict, username: str) -> list[dict]:
    ensure_crm_defaults(db)
    username = _safe_text(username)

    rows = [
        item for item in db["internal_messages"]
        if _safe_text(item.get("sender_username")) == username
    ]
    rows.sort(key=lambda x: _safe_text(x.get("created_at")), reverse=True)
    return rows


def mark_message_as_read(message_id: str) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    for item in db["internal_messages"]:
        if _safe_text(item.get("id")) == _safe_text(message_id):
            item["is_read"] = True
            persist_db(db)
            return True, "Message marked as read."

    return False, "Message not found."


# =====================================================
# CRM Tasks
# =====================================================
def create_crm_task(
    created_by: str,
    assigned_to: str,
    title: str,
    description: str = "",
    priority: str = "normal",
    due_date: str = "",
    branch: str = "",
    related_category: str = "",
) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    created_by = _safe_text(created_by)
    assigned_to = _safe_text(assigned_to)
    title = _safe_text(title)
    description = _safe_text(description)
    priority = _normalize(priority) or "normal"
    due_date = _safe_text(due_date)
    branch = _safe_text(branch)
    related_category = _normalize(related_category)

    if not created_by:
        return False, "Creator is required."

    if not assigned_to:
        return False, "Assigned user is required."

    if assigned_to not in (db.get("users") or {}):
        return False, "Assigned user not found."

    if not title:
        return False, "Task title is required."

    if priority not in DEFAULT_CRM_PRIORITIES:
        priority = "normal"

    task_id = _generate_id("crm_task")

    db["crm_records"].append(
        {
            "id": task_id,
            "title": title,
            "description": description,
            "created_by": created_by,
            "assigned_to": assigned_to,
            "priority": priority,
            "status": "new",
            "branch": branch,
            "related_category": related_category,
            "due_date": due_date,
            "comments": [],
            "status_history": [
                {
                    "status": "new",
                    "changed_by": created_by,
                    "changed_at": _now_str(),
                    "note": "Task created",
                }
            ],
            "created_at": _now_str(),
            "updated_at": _now_str(),
            "completed_at": "",
        }
    )

    add_notification(
        db=db,
        username=assigned_to,
        title="New Task Assigned",
        message=f"{created_by} assigned a task: {title}",
        related_type="crm_task",
        related_id=task_id,
    )

    persist_db(db)
    return True, "CRM task created successfully."


def get_crm_tasks(
    db: dict,
    assigned_to: str | None = None,
    created_by: str | None = None,
    status: str | None = None,
) -> list[dict]:
    ensure_crm_defaults(db)

    rows = list(db["crm_records"])

    if assigned_to:
        assigned_to = _safe_text(assigned_to)
        rows = [item for item in rows if _safe_text(item.get("assigned_to")) == assigned_to]

    if created_by:
        created_by = _safe_text(created_by)
        rows = [item for item in rows if _safe_text(item.get("created_by")) == created_by]

    if status and _normalize(status) != "all":
        status = _normalize(status)
        rows = [item for item in rows if _normalize(item.get("status")) == status]

    rows.sort(key=lambda x: _safe_text(x.get("updated_at")), reverse=True)
    return rows


def get_crm_task_by_id(db: dict, task_id: str) -> dict | None:
    ensure_crm_defaults(db)
    for item in db["crm_records"]:
        if _safe_text(item.get("id")) == _safe_text(task_id):
            return item
    return None


def update_crm_task_status(
    task_id: str,
    new_status: str,
    changed_by: str,
    note: str = "",
) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    new_status = _normalize(new_status)
    changed_by = _safe_text(changed_by)
    note = _safe_text(note)

    if new_status not in DEFAULT_CRM_TASK_STATUSES:
        return False, "Invalid task status."

    task = get_crm_task_by_id(db, task_id)
    if not task:
        return False, "Task not found."

    old_status = _normalize(task.get("status"))
    task["status"] = new_status
    task["updated_at"] = _now_str()

    if new_status == "done":
        task["completed_at"] = _now_str()

    task.setdefault("status_history", []).append(
        {
            "status": new_status,
            "changed_by": changed_by,
            "changed_at": _now_str(),
            "note": note or f"Status changed from {old_status} to {new_status}",
        }
    )

    assigned_to = _safe_text(task.get("assigned_to"))
    created_by = _safe_text(task.get("created_by"))

    if created_by and created_by != changed_by:
        add_notification(
            db=db,
            username=created_by,
            title="Task Status Updated",
            message=f"{changed_by} changed task '{task.get('title', '-')}' to {new_status}",
            related_type="crm_task",
            related_id=_safe_text(task.get("id")),
        )

    if assigned_to and assigned_to != changed_by and assigned_to != created_by:
        add_notification(
            db=db,
            username=assigned_to,
            title="Task Status Updated",
            message=f"{changed_by} changed task '{task.get('title', '-')}' to {new_status}",
            related_type="crm_task",
            related_id=_safe_text(task.get("id")),
        )

    persist_db(db)
    return True, "Task status updated successfully."


def reassign_crm_task(
    task_id: str,
    new_assignee: str,
    changed_by: str,
    note: str = "",
) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    new_assignee = _safe_text(new_assignee)
    changed_by = _safe_text(changed_by)
    note = _safe_text(note)

    if new_assignee not in (db.get("users") or {}):
        return False, "New assignee not found."

    task = get_crm_task_by_id(db, task_id)
    if not task:
        return False, "Task not found."

    old_assignee = _safe_text(task.get("assigned_to"))
    task["assigned_to"] = new_assignee
    task["updated_at"] = _now_str()

    task.setdefault("status_history", []).append(
        {
            "status": _safe_text(task.get("status")),
            "changed_by": changed_by,
            "changed_at": _now_str(),
            "note": note or f"Task reassigned from {old_assignee} to {new_assignee}",
        }
    )

    add_notification(
        db=db,
        username=new_assignee,
        title="Task Reassigned To You",
        message=f"{changed_by} reassigned task: {task.get('title', '-')}",
        related_type="crm_task",
        related_id=_safe_text(task.get("id")),
    )

    persist_db(db)
    return True, "Task reassigned successfully."


def add_crm_task_comment(
    task_id: str,
    comment_by: str,
    comment_text: str,
) -> tuple[bool, str]:
    db = load_db()
    ensure_crm_defaults(db)

    task = get_crm_task_by_id(db, task_id)
    if not task:
        return False, "Task not found."

    comment_by = _safe_text(comment_by)
    comment_text = _safe_text(comment_text)

    if not comment_text:
        return False, "Comment is required."

    task.setdefault("comments", []).append(
        {
            "id": _generate_id("comment"),
            "comment_by": comment_by,
            "comment_text": comment_text,
            "created_at": _now_str(),
        }
    )
    task["updated_at"] = _now_str()

    related_users = {
        _safe_text(task.get("created_by")),
        _safe_text(task.get("assigned_to")),
    }
    related_users.discard(comment_by)
    related_users.discard("")

    for username in related_users:
        add_notification(
            db=db,
            username=username,
            title="New Task Comment",
            message=f"{comment_by} commented on task: {task.get('title', '-')}",
            related_type="crm_task",
            related_id=_safe_text(task.get("id")),
        )

    persist_db(db)
    return True, "Comment added successfully."


# =====================================================
# Dashboard helpers
# =====================================================
def get_crm_dashboard_stats(db: dict, username: str | None = None) -> dict:
    ensure_crm_defaults(db)

    tasks = list(db["crm_records"])
    messages = list(db["internal_messages"])
    notifications = list(db["crm_notifications"])

    if username:
        username = _safe_text(username)
        my_tasks = [item for item in tasks if _safe_text(item.get("assigned_to")) == username]
        my_unread_messages = [
            item for item in messages
            if _safe_text(item.get("receiver_username")) == username and not bool(item.get("is_read", False))
        ]
        my_unread_notifications = [
            item for item in notifications
            if _safe_text(item.get("username")) == username and not bool(item.get("is_read", False))
        ]

        return {
            "my_tasks_total": len(my_tasks),
            "my_tasks_new": len([x for x in my_tasks if _normalize(x.get("status")) == "new"]),
            "my_tasks_in_progress": len([x for x in my_tasks if _normalize(x.get("status")) == "in_progress"]),
            "my_tasks_waiting": len([x for x in my_tasks if _normalize(x.get("status")) == "waiting"]),
            "my_tasks_done": len([x for x in my_tasks if _normalize(x.get("status")) == "done"]),
            "my_unread_messages": len(my_unread_messages),
            "my_unread_notifications": len(my_unread_notifications),
        }

    return {
        "total_tasks": len(tasks),
        "total_new_tasks": len([x for x in tasks if _normalize(x.get("status")) == "new"]),
        "total_in_progress_tasks": len([x for x in tasks if _normalize(x.get("status")) == "in_progress"]),
        "total_waiting_tasks": len([x for x in tasks if _normalize(x.get("status")) == "waiting"]),
        "total_done_tasks": len([x for x in tasks if _normalize(x.get("status")) == "done"]),
        "total_messages": len(messages),
        "total_notifications": len(notifications),
    }


# =====================================================
# UI helpers
# =====================================================
def _render_stats_cards(db: dict, current_user: str) -> None:
    stats = get_crm_dashboard_stats(db, current_user)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("My Tasks", stats.get("my_tasks_total", 0))
    with c2:
        st.metric("In Progress", stats.get("my_tasks_in_progress", 0))
    with c3:
        st.metric("Unread Messages", stats.get("my_unread_messages", 0))
    with c4:
        st.metric("Notifications", stats.get("my_unread_notifications", 0))


def _render_create_task_tab(db: dict, current_user: str) -> None:
    st.subheader("➕ Create Task")

    users = get_all_users(db)
    branches = db.get("branches", []) or [""]

    assigned_to = st.selectbox(
        "Assign To",
        users,
        format_func=lambda x: get_user_display_name(db, x),
        key="crm_create_assigned_to",
    )
    title = st.text_input("Task Title", key="crm_create_title")
    description = st.text_area("Description", key="crm_create_description")
    priority = st.selectbox("Priority", DEFAULT_CRM_PRIORITIES, index=1, key="crm_create_priority")
    due_date = st.text_input("Due Date", placeholder="YYYY-MM-DD", key="crm_create_due_date")
    branch = st.selectbox("Branch", branches, key="crm_create_branch")
    related_category = st.text_input("Related Category", placeholder="opening / social / hr ...", key="crm_create_related_category")

    if st.button("✅ Create CRM Task", use_container_width=True):
        success, message = create_crm_task(
            created_by=current_user,
            assigned_to=assigned_to,
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


def _render_my_tasks_tab(db: dict, current_user: str) -> None:
    st.subheader("📋 My Tasks")

    status_filter = st.selectbox(
        "Status Filter",
        ["all", "new", "in_progress", "waiting", "done", "cancelled"],
        key="crm_my_tasks_status_filter",
    )

    tasks = get_crm_tasks(db, assigned_to=current_user, status=status_filter)

    if not tasks:
        st.info("No tasks found.")
        return

    for task in tasks:
        with st.expander(f"{task.get('title', '-')} | {DEFAULT_CRM_TASK_STATUSES.get(task.get('status', ''), task.get('status', '-'))}", expanded=False):
            st.write(f"**Assigned By:** {get_user_display_name(db, task.get('created_by', ''))}")
            st.write(f"**Priority:** {task.get('priority', '-')}")
            st.write(f"**Branch:** {task.get('branch', '-') or '-'}")
            st.write(f"**Due Date:** {task.get('due_date', '-') or '-'}")
            st.write(f"**Related Category:** {task.get('related_category', '-') or '-'}")
            st.write(f"**Description:** {task.get('description', '-') or '-'}")
            st.write(f"**Created At:** {task.get('created_at', '-')}")
            st.write(f"**Updated At:** {task.get('updated_at', '-')}")

            st.divider()
            new_status = st.selectbox(
                "Update Status",
                list(DEFAULT_CRM_TASK_STATUSES.keys()),
                index=list(DEFAULT_CRM_TASK_STATUSES.keys()).index(task.get("status", "new"))
                if task.get("status", "new") in DEFAULT_CRM_TASK_STATUSES
                else 0,
                format_func=lambda x: DEFAULT_CRM_TASK_STATUSES.get(x, x),
                key=f"crm_status_{task['id']}",
            )
            status_note = st.text_input("Status Note", key=f"crm_status_note_{task['id']}")

            if st.button("💾 Save Status", key=f"crm_save_status_{task['id']}"):
                success, message = update_crm_task_status(
                    task_id=task["id"],
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
            st.markdown("**Comments**")
            comments = task.get("comments", [])
            if comments:
                for comment in comments:
                    st.info(f"{comment.get('comment_by', '-')} | {comment.get('created_at', '-')}\n\n{comment.get('comment_text', '-')}")
            else:
                st.caption("No comments yet.")

            new_comment = st.text_area("Add Comment", key=f"crm_comment_{task['id']}")
            if st.button("➕ Add Comment", key=f"crm_add_comment_{task['id']}"):
                success, message = add_crm_task_comment(
                    task_id=task["id"],
                    comment_by=current_user,
                    comment_text=new_comment,
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def _render_team_tasks_tab(db: dict, current_user: str) -> None:
    st.subheader("👥 Team Tasks")

    all_users = ["all"] + get_all_users(db)
    selected_user = st.selectbox(
        "Assigned User",
        all_users,
        format_func=lambda x: "All Users" if x == "all" else get_user_display_name(db, x),
        key="crm_team_assigned_filter",
    )
    selected_status = st.selectbox(
        "Task Status",
        ["all", "new", "in_progress", "waiting", "done", "cancelled"],
        key="crm_team_status_filter",
    )

    tasks = get_crm_tasks(
        db,
        assigned_to=None if selected_user == "all" else selected_user,
        status=selected_status,
    )

    if not tasks:
        st.info("No tasks found.")
        return

    users = get_all_users(db)

    for task in tasks:
        with st.expander(
            f"{task.get('title', '-')} | {get_user_display_name(db, task.get('assigned_to', ''))}",
            expanded=False,
        ):
            st.write(f"**Created By:** {get_user_display_name(db, task.get('created_by', ''))}")
            st.write(f"**Assigned To:** {get_user_display_name(db, task.get('assigned_to', ''))}")
            st.write(f"**Status:** {DEFAULT_CRM_TASK_STATUSES.get(task.get('status', ''), task.get('status', '-'))}")
            st.write(f"**Priority:** {task.get('priority', '-')}")
            st.write(f"**Description:** {task.get('description', '-') or '-'}")

            new_assignee = st.selectbox(
                "Reassign To",
                users,
                index=users.index(task.get("assigned_to"))
                if task.get("assigned_to") in users
                else 0,
                format_func=lambda x: get_user_display_name(db, x),
                key=f"crm_reassign_to_{task['id']}",
            )
            reassign_note = st.text_input("Reassign Note", key=f"crm_reassign_note_{task['id']}")

            if st.button("🔄 Reassign Task", key=f"crm_reassign_btn_{task['id']}"):
                success, message = reassign_crm_task(
                    task_id=task["id"],
                    new_assignee=new_assignee,
                    changed_by=current_user,
                    note=reassign_note,
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def _render_messages_tab(db: dict, current_user: str) -> None:
    st.subheader("✉ Internal Messages")

    send_tab, inbox_tab, sent_tab = st.tabs(["Send", "Inbox", "Sent"])

    with send_tab:
        users = [u for u in get_all_users(db) if u != current_user]

        if not users:
            st.info("No users available.")
        else:
            receiver = st.selectbox(
                "To",
                users,
                format_func=lambda x: get_user_display_name(db, x),
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

    with inbox_tab:
        inbox = get_inbox_messages(db, current_user)

        if not inbox:
            st.info("Inbox is empty.")
        else:
            for item in inbox:
                with st.expander(
                    f"{item.get('subject', '-')} | From: {get_user_display_name(db, item.get('sender_username', ''))}",
                    expanded=False,
                ):
                    st.write(f"**From:** {get_user_display_name(db, item.get('sender_username', ''))}")
                    st.write(f"**Date:** {item.get('created_at', '-')}")
                    st.write(item.get("message_text", "-"))

                    if not bool(item.get("is_read", False)):
                        if st.button("✅ Mark as Read", key=f"crm_mark_msg_read_{item['id']}"):
                            success, message = mark_message_as_read(item["id"])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

    with sent_tab:
        sent = get_sent_messages(db, current_user)

        if not sent:
            st.info("No sent messages.")
        else:
            for item in sent:
                with st.expander(
                    f"{item.get('subject', '-')} | To: {get_user_display_name(db, item.get('receiver_username', ''))}",
                    expanded=False,
                ):
                    st.write(f"**To:** {get_user_display_name(db, item.get('receiver_username', ''))}")
                    st.write(f"**Date:** {item.get('created_at', '-')}")
                    st.write(item.get("message_text", "-"))


def _render_notifications_tab(db: dict, current_user: str) -> None:
    st.subheader("🔔 Notifications")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("✅ Mark All Read", use_container_width=True):
            success, message = mark_all_notifications_as_read(current_user)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    notifications = get_user_notifications(db, current_user, unread_only=False)

    if not notifications:
        st.info("No notifications.")
        return

    for item in notifications:
        unread_flag = "🟢" if not bool(item.get("is_read", False)) else "⚪"
        with st.expander(f"{unread_flag} {item.get('title', '-')}", expanded=False):
            st.write(f"**Date:** {item.get('created_at', '-')}")
            st.write(item.get("message", "-"))

            if not bool(item.get("is_read", False)):
                if st.button("Mark as Read", key=f"crm_mark_notif_{item['id']}"):
                    success, message = mark_notification_as_read(item["id"])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)


def _render_reports_tab(db: dict) -> None:
    st.subheader("📊 CRM Summary")

    stats = get_crm_dashboard_stats(db)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Tasks", stats.get("total_tasks", 0))
    with c2:
        st.metric("New", stats.get("total_new_tasks", 0))
    with c3:
        st.metric("In Progress", stats.get("total_in_progress_tasks", 0))
    with c4:
        st.metric("Done", stats.get("total_done_tasks", 0))

    st.divider()

    tasks = get_crm_tasks(db)

    if tasks:
        df = pd.DataFrame(
            [
                {
                    "Title": item.get("title", "-"),
                    "Assigned To": get_user_display_name(db, item.get("assigned_to", "")),
                    "Created By": get_user_display_name(db, item.get("created_by", "")),
                    "Status": DEFAULT_CRM_TASK_STATUSES.get(item.get("status", ""), item.get("status", "-")),
                    "Priority": item.get("priority", "-"),
                    "Branch": item.get("branch", "-"),
                    "Due Date": item.get("due_date", "-"),
                    "Updated At": item.get("updated_at", "-"),
                }
                for item in tasks
            ]
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No CRM task data yet.")


# =====================================================
# Main CRM UI
# =====================================================
def render_crm_module() -> None:
    db = load_db()
    changed = ensure_crm_defaults(db)
    if changed:
        persist_db(db)
        db = load_db()

    current_user = get_current_username()
    current_role = _normalize(get_current_role())

    if not current_user:
        st.error("You must be logged in.")
        return

    st.title("📇 CRM & Internal Communication")
    st.caption("مهام داخلية، مراسلات، إشعارات، ومتابعة العمل بين الموظفين والإدارة.")

    _render_stats_cards(db, current_user)
    st.divider()

    is_admin_like = current_role in ["admin", "manager", "hr"]

    if is_admin_like:
        tabs = st.tabs(
            [
                "Create Task",
                "My Tasks",
                "Team Tasks",
                "Messages",
                "Notifications",
                "Reports",
            ]
        )

        with tabs[0]:
            _render_create_task_tab(db, current_user)
        with tabs[1]:
            _render_my_tasks_tab(db, current_user)
        with tabs[2]:
            _render_team_tasks_tab(db, current_user)
        with tabs[3]:
            _render_messages_tab(db, current_user)
        with tabs[4]:
            _render_notifications_tab(db, current_user)
        with tabs[5]:
            _render_reports_tab(db)

    else:
        tabs = st.tabs(
            [
                "My Tasks",
                "Messages",
                "Notifications",
            ]
        )

        with tabs[0]:
            _render_my_tasks_tab(db, current_user)
        with tabs[1]:
            _render_messages_tab(db, current_user)
        with tabs[2]:
            _render_notifications_tab(db, current_user)
