# =====================================================
# TASK SERVICE
# Supabase-backed task operations
# Supports dynamic task categories
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


def _normalize_category_name(category: str) -> str:
    return str(category or "").strip().lower()


def _is_valid_category(category: str) -> bool:
    # دعم ديناميكي:
    # أي category غير فاضية تعتبر صالحة
    return bool(_normalize_category_name(category))


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
        normalized_category = _normalize_category_name(category)

        for task_text in task_list:
            cleaned = str(task_text).strip()
            if cleaned:
                rows.append(
                    {
                        "category": normalized_category,
                        "task_text": cleaned,
                    }
                )

    if rows:
        _run_with_retry(lambda: supabase.table("tasks").insert(rows).execute())


# =====================================================
# Categories
# =====================================================
def get_all_task_categories() -> List[str]:
    _ensure_seeded_once_if_empty()
    supabase = get_supabase()

    result = _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .select("category")
            .order("category")
            .execute()
        )
    )

    rows = result.data or []

    categories = []
    seen = set()

    # أولاً: التصنيفات الموجودة فعليًا في قاعدة البيانات
    for row in rows:
        category = _normalize_category_name(row.get("category", ""))
        if category and category not in seen:
            seen.add(category)
            categories.append(category)

    # ثانياً: نضمن ظهور التصنيفات الأساسية القديمة حتى لو الجدول لسه فاضي جزئيًا
    for category in TASK_CATEGORIES:
        normalized_category = _normalize_category_name(category)
        if normalized_category and normalized_category not in seen:
            seen.add(normalized_category)
            categories.append(normalized_category)

    return categories


# =====================================================
# Read
# =====================================================
def get_tasks_by_category(category: str) -> List[Dict]:
    normalized_category = _normalize_category_name(category)

    if not _is_valid_category(normalized_category):
        return []

    _ensure_seeded_once_if_empty()
    supabase = get_supabase()

    result = _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .select("id, category, task_text, created_at")
            .eq("category", normalized_category)
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
    grouped: Dict[str, List[str]] = {}

    # نبدأ بالتصنيفات الأساسية القديمة
    for category in TASK_CATEGORIES:
        grouped[_normalize_category_name(category)] = []

    # ونضيف أي تصنيفات ديناميكية جديدة
    for row in rows:
        category = _normalize_category_name(row.get("category", ""))
        task_text = str(row.get("task_text", "")).strip()

        if not category or not task_text:
            continue

        grouped.setdefault(category, [])
        grouped[category].append(task_text)

    return grouped


# =====================================================
# Create
# =====================================================
def add_task(category: str, task_text: str) -> tuple[bool, str]:
    normalized_category = _normalize_category_name(category)

    if not _is_valid_category(normalized_category):
        return False, "Task category is required."

    cleaned_task = str(task_text).strip()
    if not cleaned_task:
        return False, "Task text cannot be empty."

    supabase = get_supabase()

    existing = _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .select("id")
            .eq("category", normalized_category)
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
                "category": normalized_category,
                "task_text": cleaned_task,
            }
        ).execute()
    )

    return True, "Task added successfully."


def create_category(category: str) -> tuple[bool, str]:
    normalized_category = _normalize_category_name(category)

    if not normalized_category:
        return False, "Category name is required."

    # بما إن مفيش جدول مستقل للتصنيفات،
    # إنشاء category بيتم ضمنيًا عند إضافة أول task لها.
    existing_tasks = get_tasks_by_category(normalized_category)
    if existing_tasks:
        return True, "Category already exists."

    placeholder_task = "__category_placeholder__"
    success, message = add_task(normalized_category, placeholder_task)
    if not success:
        return False, message

    # نحذف الـ placeholder فورًا
    refreshed = get_tasks_by_category(normalized_category)
    for row in refreshed:
        if row.get("task_text") == placeholder_task and row.get("id"):
            delete_task(row["id"])

    return True, "Category created successfully."


# =====================================================
# Update
# =====================================================
def update_task(task_id: str, new_task_text: str) -> tuple[bool, str]:
    if not task_id:
        return False, "Task ID is required."

    cleaned_task = str(new_task_text).strip()
    if not cleaned_task:
        return False, "Task text cannot be empty."

    supabase = get_supabase()

    _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .update({"task_text": cleaned_task})
            .eq("id", task_id)
            .execute()
        )
    )

    return True, "Task updated successfully."


def rename_category(old_category: str, new_category: str) -> tuple[bool, str]:
    old_normalized = _normalize_category_name(old_category)
    new_normalized = _normalize_category_name(new_category)

    if not old_normalized:
        return False, "Old category is required."

    if not new_normalized:
        return False, "New category is required."

    if old_normalized == new_normalized:
        return False, "No category change detected."

    supabase = get_supabase()

    rows = get_tasks_by_category(old_normalized)
    if not rows:
        return False, "Old category was not found."

    _run_with_retry(
        lambda: (
            supabase.table("tasks")
            .update({"category": new_normalized})
            .eq("category", old_normalized)
            .execute()
        )
    )

    return True, "Category renamed successfully."


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


def delete_category(category: str) -> tuple[bool, str]:
    normalized_category = _normalize_category_name(category)

    if not normalized_category:
        return False, "Category is required."

    supabase = get_supabase()

    _run_with_retry(
        lambda: supabase.table("tasks").delete().eq("category", normalized_category).execute()
    )

    return True, "Category deleted successfully."


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
    normalized_category = _normalize_category_name(category)

    if not _is_valid_category(normalized_category):
        return False, "Task category is required."

    supabase = get_supabase()

    cleaned_tasks = []
    seen = set()

    for task in task_texts:
        cleaned = str(task).strip()
        if cleaned and cleaned not in seen:
            cleaned_tasks.append(cleaned)
            seen.add(cleaned)

    _run_with_retry(
        lambda: supabase.table("tasks").delete().eq("category", normalized_category).execute()
    )

    if cleaned_tasks:
        _run_with_retry(
            lambda: supabase.table("tasks").insert(
                [{"category": normalized_category, "task_text": task} for task in cleaned_tasks]
            ).execute()
        )

    return True, "Category tasks replaced successfully."
