# =====================================================
# CRM SERVICE
# Internal tasks, messages, notifications, and dashboard helpers
# =====================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

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
