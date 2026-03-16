# =====================================================
# CRM SERVICE
# Internal tasks, messages, notifications, and dashboard helpers
# Optimized version - direct Supabase helpers
# =====================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

from database import (
    load_users_only,
    load_crm_tasks,
    load_crm_task_by_id,
    load_internal_messages,
    load_notifications,
    insert_crm_task,
    update_crm_task_row,
    insert_internal_message_row,
    insert_notification_row,
    mark_notification_read_row,
    mark_all_notifications_read_for_user,
    mark_message_read_row,
    append_crm_task_comment,
)


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
    return datetime.utcnow().isoformat()


def _generate_id(prefix: str) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}_{stamp}"


def _get_users_map() -> dict:
    try:
        return load_users_only() or {}
    except Exception:
        return {}


# =====================================================
# User helpers
# =====================================================
def get_all_users(db: dict | None = None) -> list[str]:
    users = db.get("users", {}) if isinstance(db, dict) and db.get("users") else _get_users_map()
    return sorted(list(users.keys()))


def get_user_role(db: dict | None, username: str) -> str:
    users = db.get("users", {}) if isinstance(db, dict) and db.get("users") else _get_users_map()
    return _normalize((users.get(username) or {}).get("role"))


def get_user_full_name(db: dict | None, username: str) -> str:
    users = db.get("users", {}) if isinstance(db, dict) and db.get("users") else _get_users_map()
    user = users.get(username, {})
    return _safe_text(user.get("full_name"), username)


def get_user_display_name(db: dict | None, username: str) -> str:
    full_name = get_user_full_name(db, username)
    return f"{full_name} ({username})"


# =====================================================
# Notifications
# =====================================================
def add_notification(
    db: dict | None,
    username: str,
    title: str,
    message: str,
    related_type: str = "",
    related_id: str = "",
) -> tuple[bool, str]:
    payload = {
        "id": _generate_id("notif"),
        "username": _safe_text(username),
        "title": _safe_text(title),
        "message": _safe_text(message),
        "related_type": _safe_text(related_type),
        "related_id": _safe_text(related_id),
        "is_read": False,
        "created_at": _now_str(),
        "read_at": None,
    }
    return insert_notification_row(payload)


def get_user_notifications(db: dict | None, username: str, unread_only: bool = False) -> list[dict]:
    username = _safe_text(username)
    if not username:
        return []
    return load_notifications(username=username, unread_only=unread_only)


def mark_notification_as_read(notification_id: str) -> tuple[bool, str]:
    if not _safe_text(notification_id):
        return False, "Notification ID is required."
    return mark_notification_read_row(notification_id)


def mark_all_notifications_as_read(username: str) -> tuple[bool, str]:
    username = _safe_text(username)
    if not username:
        return False, "Username is required."
    return mark_all_notifications_read_for_user(username)


# =====================================================
# Internal Messages
# =====================================================
def send_internal_message(
    sender_username: str,
    receiver_username: str,
    subject: str,
    message_text: str,
) -> tuple[bool, str]:
    users = _get_users_map()

    sender_username = _safe_text(sender_username)
    receiver_username = _safe_text(receiver_username)
    subject = _safe_text(subject)
    message_text = _safe_text(message_text)

    if not sender_username:
        return False, "Sender is required."

    if not receiver_username:
        return False, "Receiver is required."

    if receiver_username not in users:
        return False, "Receiver not found."

    if not subject:
        return False, "Subject is required."

    if not message_text:
        return False, "Message body is required."

    message_id = _generate_id("msg")

    message_payload = {
        "id": message_id,
        "sender_username": sender_username,
        "receiver_username": receiver_username,
        "subject": subject,
        "message_text": message_text,
        "is_read": False,
        "created_at": _now_str(),
        "read_at": None,
    }

    ok, msg = insert_internal_message_row(message_payload)
    if not ok:
        return False, msg

    add_notification(
        db=None,
        username=receiver_username,
        title="New Internal Message",
        message=f"{sender_username} sent you a message: {subject}",
        related_type="message",
        related_id=message_id,
    )

    return True, "Message sent successfully."


def get_inbox_messages(db: dict | None, username: str) -> list[dict]:
    username = _safe_text(username)
    if not username:
        return []
    return load_internal_messages(receiver_username=username)


def get_sent_messages(db: dict | None, username: str) -> list[dict]:
    username = _safe_text(username)
    if not username:
        return []
    return load_internal_messages(sender_username=username)


def mark_message_as_read(message_id: str) -> tuple[bool, str]:
    if not _safe_text(message_id):
        return False, "Message ID is required."
    return mark_message_read_row(message_id)


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
    users = _get_users_map()

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

    if assigned_to not in users:
        return False, "Assigned user not found."

    if not title:
        return False, "Task title is required."

    if priority not in DEFAULT_CRM_PRIORITIES:
        priority = "normal"

    task_id = _generate_id("crm_task")

    task_payload = {
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
        "completed_at": None,
    }

    ok, msg = insert_crm_task(task_payload)
    if not ok:
        return False, msg

    add_notification(
        db=None,
        username=assigned_to,
        title="New Task Assigned",
        message=f"{created_by} assigned a task: {title}",
        related_type="crm_task",
        related_id=task_id,
    )

    return True, "CRM task created successfully."


def get_crm_tasks(
    db: dict | None = None,
    assigned_to: str | None = None,
    created_by: str | None = None,
    status: str | None = None,
) -> list[dict]:
    return load_crm_tasks(
        assigned_to=_safe_text(assigned_to) if assigned_to else None,
        created_by=_safe_text(created_by) if created_by else None,
        status=_normalize(status) if status else None,
    )


def get_crm_task_by_id(db: dict | None, task_id: str) -> dict | None:
    if not _safe_text(task_id):
        return None
    return load_crm_task_by_id(task_id)


def update_crm_task_status(
    task_id: str,
    new_status: str,
    changed_by: str,
    note: str = "",
) -> tuple[bool, str]:
    task_id = _safe_text(task_id)
    new_status = _normalize(new_status)
    changed_by = _safe_text(changed_by)
    note = _safe_text(note)

    if not task_id:
        return False, "Task ID is required."

    if new_status not in DEFAULT_CRM_TASK_STATUSES:
        return False, "Invalid task status."

    task = load_crm_task_by_id(task_id)
    if not task:
        return False, "Task not found."

    old_status = _normalize(task.get("status"))

    status_history = list(task.get("status_history", []))
    status_history.append(
        {
            "status": new_status,
            "changed_by": changed_by,
            "changed_at": _now_str(),
            "note": note or f"Status changed from {old_status} to {new_status}",
        }
    )

    patch_data = {
        "status": new_status,
        "status_history": status_history,
    }

    if new_status == "done":
        patch_data["completed_at"] = _now_str()
    else:
        patch_data["completed_at"] = None

    ok, msg = update_crm_task_row(task_id, patch_data)
    if not ok:
        return False, msg

    assigned_to = _safe_text(task.get("assigned_to"))
    created_by = _safe_text(task.get("created_by"))

    if created_by and created_by != changed_by:
        add_notification(
            db=None,
            username=created_by,
            title="Task Status Updated",
            message=f"{changed_by} changed task '{task.get('title', '-')}' to {new_status}",
            related_type="crm_task",
            related_id=_safe_text(task.get("id")),
        )

    if assigned_to and assigned_to != changed_by and assigned_to != created_by:
        add_notification(
            db=None,
            username=assigned_to,
            title="Task Status Updated",
            message=f"{changed_by} changed task '{task.get('title', '-')}' to {new_status}",
            related_type="crm_task",
            related_id=_safe_text(task.get("id")),
        )

    return True, "Task status updated successfully."


def reassign_crm_task(
    task_id: str,
    new_assignee: str,
    changed_by: str,
    note: str = "",
) -> tuple[bool, str]:
    users = _get_users_map()

    task_id = _safe_text(task_id)
    new_assignee = _safe_text(new_assignee)
    changed_by = _safe_text(changed_by)
    note = _safe_text(note)

    if not task_id:
        return False, "Task ID is required."

    if new_assignee not in users:
        return False, "New assignee not found."

    task = load_crm_task_by_id(task_id)
    if not task:
        return False, "Task not found."

    old_assignee = _safe_text(task.get("assigned_to"))

    status_history = list(task.get("status_history", []))
    status_history.append(
        {
            "status": _safe_text(task.get("status")),
            "changed_by": changed_by,
            "changed_at": _now_str(),
            "note": note or f"Task reassigned from {old_assignee} to {new_assignee}",
        }
    )

    ok, msg = update_crm_task_row(
        task_id,
        {
            "assigned_to": new_assignee,
            "status_history": status_history,
        },
    )
    if not ok:
        return False, msg

    add_notification(
        db=None,
        username=new_assignee,
        title="Task Reassigned To You",
        message=f"{changed_by} reassigned task: {task.get('title', '-')}",
        related_type="crm_task",
        related_id=_safe_text(task.get("id")),
    )

    return True, "Task reassigned successfully."


def add_crm_task_comment(
    task_id: str,
    comment_by: str,
    comment_text: str,
) -> tuple[bool, str]:
    task_id = _safe_text(task_id)
    comment_by = _safe_text(comment_by)
    comment_text = _safe_text(comment_text)

    if not task_id:
        return False, "Task ID is required."

    task = load_crm_task_by_id(task_id)
    if not task:
        return False, "Task not found."

    if not comment_text:
        return False, "Comment is required."

    comment_payload = {
        "id": _generate_id("comment"),
        "comment_by": comment_by,
        "comment_text": comment_text,
        "created_at": _now_str(),
    }

    ok, msg = append_crm_task_comment(task_id, comment_payload)
    if not ok:
        return False, msg

    related_users = {
        _safe_text(task.get("created_by")),
        _safe_text(task.get("assigned_to")),
    }
    related_users.discard(comment_by)
    related_users.discard("")

    for username in related_users:
        add_notification(
            db=None,
            username=username,
            title="New Task Comment",
            message=f"{comment_by} commented on task: {task.get('title', '-')}",
            related_type="crm_task",
            related_id=_safe_text(task.get("id")),
        )

    return True, "Comment added successfully."


# =====================================================
# Dashboard helpers
# =====================================================
def get_crm_dashboard_stats(db: dict | None = None, username: str | None = None) -> dict:
    tasks = load_crm_tasks()
    messages = load_internal_messages()

    if username:
        username = _safe_text(username)
        notifications = load_notifications(username=username, unread_only=False)

        my_tasks = [item for item in tasks if _safe_text(item.get("assigned_to")) == username]
        my_unread_messages = [
            item for item in messages
            if _safe_text(item.get("receiver_username")) == username and not bool(item.get("is_read", False))
        ]
        my_unread_notifications = [
            item for item in notifications
            if not bool(item.get("is_read", False))
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

    all_notifications = []
    try:
        # لو حبيت بعدين تضيف loader لكل الإشعارات بدون username
        # تقدر تبدله هنا بسهولة
        all_notifications = []
    except Exception:
        all_notifications = []

    return {
        "total_tasks": len(tasks),
        "total_new_tasks": len([x for x in tasks if _normalize(x.get("status")) == "new"]),
        "total_in_progress_tasks": len([x for x in tasks if _normalize(x.get("status")) == "in_progress"]),
        "total_waiting_tasks": len([x for x in tasks if _normalize(x.get("status")) == "waiting"]),
        "total_done_tasks": len([x for x in tasks if _normalize(x.get("status")) == "done"]),
        "total_messages": len(messages),
        "total_notifications": len(all_notifications),
    }
