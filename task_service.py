# =====================================================
# TASK SERVICE
# Supabase-backed task operations
# =====================================================

from typing import List, Dict, Optional

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


# =====================================================
# Read
# =====================================================
def get_tasks_by_category(category: str) -> List[Dict]:
    if not _is_valid_category(category):
        return []

    supabase = get_supabase()

    result = (
        supabase.table("tasks")
        .select("id, category, task_text, created_at")
        .eq("category", category)
        .order("created_at")
        .execute()
    )

    rows = result.data or []
    return [_normalize_task_row(row) for row in rows]


def get_all_tasks_grouped() -> Dict[str, List[str]]:
    supabase = get_supabase()

    result = (
        supabase.table("tasks")
        .select("id, category, task_text, created_at")
        .order("created_at")
        .execute()
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

    # منع التكرار داخل نفس الفئة
    existing = (
        supabase.table("tasks")
        .select("id")
        .eq("category", category)
        .eq("task_text", cleaned_task)
        .limit(1)
        .execute()
    )

    if existing.data:
        return False, "Task already exists in this category."

    supabase.table("tasks").insert(
        {
            "category": category,
            "task_text": cleaned_task,
        }
    ).execute()

    return True, "Task added successfully."


# =====================================================
# Delete
# =====================================================
def delete_task(task_id: str) -> tuple[bool, str]:
    if not task_id:
        return False, "Task ID is required."

    supabase = get_supabase()

    supabase.table("tasks").delete().eq("id", task_id).execute()
    return True, "Task deleted successfully."


# =====================================================
# Seed defaults
# =====================================================
def seed_default_tasks_if_empty() -> tuple[bool, str]:
    supabase = get_supabase()

    existing = supabase.table("tasks").select("id").limit(1).execute()
    if existing.data:
        return True, "Tasks already exist."

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
        supabase.table("tasks").insert(rows).execute()

    return True, "Default tasks seeded successfully."


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

    supabase.table("tasks").delete().eq("category", category).execute()

    if cleaned_tasks:
        supabase.table("tasks").insert(
            [{"category": category, "task_text": task} for task in cleaned_tasks]
        ).execute()

    return True, "Category tasks replaced successfully."
