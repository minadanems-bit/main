# =====================================================
# BIRTHDAY SERVICE
# Birthday detection, wishes, and celebration helpers
# =====================================================

from __future__ import annotations

from datetime import datetime, date

from database import load_db, save_db


# =====================================================
# Helpers
# =====================================================
def _safe_text(value, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _normalize(value: str | None) -> str:
    return str(value or "").strip().lower()


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today_date() -> date:
    return date.today()


def _generate_id(prefix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}_{stamp}"


def ensure_birthday_defaults(db: dict) -> bool:
    changed = False

    if "birthday_messages" not in db or not isinstance(db.get("birthday_messages"), list):
        db["birthday_messages"] = []
        changed = True

    return changed


def persist_db(db: dict) -> None:
    save_db(db)


# =====================================================
# Date helpers
# =====================================================
def parse_birth_date(value: str | None):
    raw = _safe_text(value)
    if not raw:
        return None

    try:
        return date.fromisoformat(raw)
    except Exception:
        return None


def is_today_birthday(birth_date_value: str | None) -> bool:
    birth_date = parse_birth_date(birth_date_value)
    if not birth_date:
        return False

    today = _today_date()
    return birth_date.month == today.month and birth_date.day == today.day


# =====================================================
# User birthday helpers
# =====================================================
def get_birthday_users(db: dict) -> list[dict]:
    ensure_birthday_defaults(db)

    users = db.get("users", {}) or {}
    result = []

    for username, user_data in users.items():
        if is_today_birthday(user_data.get("birth_date")):
            result.append(
                {
                    "username": username,
                    "full_name": _safe_text(user_data.get("full_name"), username),
                    "role": _safe_text(user_data.get("role"), "employee"),
                    "birth_date": _safe_text(user_data.get("birth_date")),
                }
            )

    return result


def is_username_birthday_today(db: dict, username: str) -> bool:
    users = db.get("users", {}) or {}
    user_data = users.get(username, {})
    return is_today_birthday(user_data.get("birth_date"))


# =====================================================
# Birthday messages
# =====================================================
def send_birthday_message(
    sender_username: str,
    receiver_username: str,
    message_text: str,
) -> tuple[bool, str]:
    db = load_db()
    ensure_birthday_defaults(db)

    sender_username = _safe_text(sender_username)
    receiver_username = _safe_text(receiver_username)
    message_text = _safe_text(message_text)

    if not sender_username:
        return False, "Sender is required."

    if not receiver_username:
        return False, "Receiver is required."

    if receiver_username not in (db.get("users") or {}):
        return False, "Birthday employee not found."

    if not is_username_birthday_today(db, receiver_username):
        return False, "This employee does not have a birthday today."

    if not message_text:
        return False, "Message cannot be empty."

    db["birthday_messages"].append(
        {
            "id": _generate_id("birthday"),
            "sender_username": sender_username,
            "receiver_username": receiver_username,
            "message_text": message_text,
            "created_at": _now_str(),
        }
    )

    save_db(db)
    return True, "Birthday message sent successfully."


def get_birthday_messages_for_user(db: dict, username: str) -> list[dict]:
    ensure_birthday_defaults(db)

    username = _safe_text(username)
    rows = [
        item for item in db.get("birthday_messages", [])
        if _safe_text(item.get("receiver_username")) == username
    ]

    rows.sort(key=lambda x: _safe_text(x.get("created_at")), reverse=True)
    return rows


def get_birthday_messages_count(db: dict, username: str) -> int:
    return len(get_birthday_messages_for_user(db, username))
