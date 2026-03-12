# =====================================================
# TASK SERVICE
# Supabase-backed task operations
# =====================================================

from typing import List, Dict
import time

from httpx import RemoteProtocolError

from constants import DEFAULT_TASKS, TASK_CATEGORIES
from database import get_supabase


# =====================================================
# Helpers
# =====================================================
def _normalize_task_row(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "category": row.get("category", ""),
        "task_text": row.get("task_text", ""),
        "created_at": row.get("created_at"),
    }


def _is_valid_category(category: str) -> bool:
    return category in TASK_CATEGORIES


def _run_with_retry(action, retries: int = 3, delay: float = 0.6):
    last_error = None
    for attempt in range(retries):
        try:
            return action()
        except RemoteProtocolError as e:
            last_error = e
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
        except Exception as e:
            last_error = e
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
    if last_error:
        raise last_error


def _ensure_seeded_once_if_empty() -> None:
    supabase = get_supabase()

    existing = _run_with_retry(
        lambda: supabase.table("tasks").select("id").limit(1).execute()
    )

    if existing.data:
        return

    rows = []
    for category, task_list in DEFAULT_TASKS.items():
        for task_text in task_list:
            cleaned = str(task_text).strip()
            if cleaned:
                rows.append(
                    {
                        "category": category,
                        "task_text": cleaned,
                    }
                )

    if rows:
        _run_with_retry(lambda: supabase.table("tasks").insert(rows).execute())


# =====================================================
# Read
# =====================================================
def get_tasks_by_category(category: str) -> List[Dict]:
    if not _is_valid_category(category):
        return []

    _ensure_seeded_once_if_empty()
    supabase = get_supabase()

    result = _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .select("id, category, task_text, created_at")
            .eq("category", category)
            .order("created_at")
            .execute()
        )
    )

    rows = result.data or []
    return [_normalize_task_row(row) for row in rows]


def get_all_tasks_grouped() -> Dict[str, List[str]]:
    _ensure_seeded_once_if_empty()
    supabase = get_supabase()

    result = _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .select("id, category, task_text, created_at")
            .order("created_at")
            .execute()
        )
    )

    rows = result.data or []

    grouped = {category: [] for category in TASK_CATEGORIES}

    for row in rows:
        category = row.get("category", "")
        task_text = row.get("task_text", "")
        if category in grouped and task_text:
            grouped[category].append(task_text)

    return grouped


# =====================================================
# Create
# =====================================================
def add_task(category: str, task_text: str) -> tuple[bool, str]:
    if not _is_valid_category(category):
        return False, "Invalid task category."

    cleaned_task = str(task_text).strip()
    if not cleaned_task:
        return False, "Task text cannot be empty."

    supabase = get_supabase()

    existing = _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .select("id")
            .eq("category", category)
            .eq("task_text", cleaned_task)
            .limit(1)
            .execute()
        )
    )

    if existing.data:
        return False, "Task already exists in this category."

    _run_with_retry(
        lambda: supabase.table("tasks").insert(
            {
                "category": category,
                "task_text": cleaned_task,
            }
        ).execute()
    )

    return True, "Task added successfully."


# =====================================================
# Delete
# =====================================================
def delete_task(task_id: str) -> tuple[bool, str]:
    if not task_id:
        return False, "Task ID is required."

    supabase = get_supabase()

    _run_with_retry(
        lambda: supabase.table("tasks").delete().eq("id", task_id).execute()
    )
    return True, "Task deleted successfully."


# =====================================================
# Seed defaults
# =====================================================
def seed_default_tasks_if_empty() -> tuple[bool, str]:
    try:
        _ensure_seeded_once_if_empty()
        return True, "Default tasks seeded successfully."
    except Exception as e:
        return False, f"Failed to seed default tasks: {e}"


# =====================================================
# Replace full category
# =====================================================
def replace_category_tasks(category: str, task_texts: List[str]) -> tuple[bool, str]:
    if not _is_valid_category(category):
        return False, "Invalid task category."

    supabase = get_supabase()

    cleaned_tasks = []
    seen = set()

    for task in task_texts:
        cleaned = str(task).strip()
        if cleaned and cleaned not in seen:
            cleaned_tasks.append(cleaned)
            seen.add(cleaned)

    _run_with_retry(
        lambda: supabase.table("tasks").delete().eq("category", category).execute()
    )

    if cleaned_tasks:
        _run_with_retry(
            lambda: supabase.table("tasks").insert(
                [{"category": category, "task_text": task} for task in cleaned_tasks]
            ).execute()
        )

    return True, "Category tasks replaced successfully."
