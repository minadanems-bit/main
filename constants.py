# =====================================================
# PROJECT CONSTANTS
# =====================================================

from datetime import date


# =====================================================
# General
# =====================================================
APP_NAME = "NMS ERP"
APP_SUBTITLE = "Branch Operations & HR System"

DEFAULT_DATE_STR = str(date.today())
DEFAULT_HIRING_DATE = "2024-01-01"
DEFAULT_MANAGER_PHONE = "+971522045638"


# =====================================================
# Roles
# =====================================================
ROLE_ADMIN = "admin"
ROLE_USER = "user"

ROLE_OPTIONS = [ROLE_ADMIN, ROLE_USER]


# =====================================================
# Shift Options
# =====================================================
SHIFT_MORNING = "Morning"
SHIFT_BETWEEN = "Between"
SHIFT_NIGHT = "Night"

SHIFT_OPTIONS = [
    SHIFT_MORNING,
    SHIFT_BETWEEN,
    SHIFT_NIGHT,
]


# =====================================================
# Task Categories
# =====================================================
TASK_OPENING = "opening"
TASK_CLOSING = "closing"
TASK_SOCIAL = "social"
TASK_INTERACTION = "interaction"

TASK_CATEGORIES = [
    TASK_OPENING,
    TASK_CLOSING,
    TASK_SOCIAL,
    TASK_INTERACTION,
]


# =====================================================
# HR Record Types
# =====================================================
HR_BONUS = "bonus"
HR_DEDUCTIONS = "deductions"
HR_OVERTIME = "overtime"
HR_EXTRA_LEAVES = "extra_leaves"

HR_RECORD_KEYS = [
    HR_BONUS,
    HR_DEDUCTIONS,
    HR_OVERTIME,
    HR_EXTRA_LEAVES,
]

HR_RECORD_LABELS = {
    HR_BONUS: "Bonus",
    HR_DEDUCTIONS: "Deduction",
    HR_OVERTIME: "Overtime",
    HR_EXTRA_LEAVES: "Extra Leave",
}

HR_FORM_TO_DB_KEY = {
    "Bonus": HR_BONUS,
    "Deduction": HR_DEDUCTIONS,
    "Overtime": HR_OVERTIME,
    "Extra Leave": HR_EXTRA_LEAVES,
}


# =====================================================
# Payroll Entry UI Labels
# =====================================================
PAYROLL_ENTRY_OPTIONS = [
    "Bonus 🎁",
    "Deductions ⚠️",
    "Overtime ⏳",
    "Extra Leave 🏖️",
]

PAYROLL_ENTRY_KEY_MAP = {
    "Bonus 🎁": HR_BONUS,
    "Deductions ⚠️": HR_DEDUCTIONS,
    "Overtime ⏳": HR_OVERTIME,
    "Extra Leave 🏖️": HR_EXTRA_LEAVES,
}


# =====================================================
# Admin Modules
# =====================================================
ADMIN_MODULE_HR = "👥 Manage Employees (HR)"
ADMIN_MODULE_PAYROLL = "💰 Payroll & Money"
ADMIN_MODULE_TASKS = "📝 Tasks & Checklists"
ADMIN_MODULE_BRANCHES = "🏢 Branches & Expenses"
ADMIN_MODULE_PRINTERS = "🖨 Printer Management"
ADMIN_MODULE_ARCHIVE = "📂 Archive & History"
ADMIN_MODULE_TRAINING = "🎓 Employee Training"

ADMIN_MODULE_OPTIONS = [
    ADMIN_MODULE_HR,
    ADMIN_MODULE_PAYROLL,
    ADMIN_MODULE_TASKS,
    ADMIN_MODULE_BRANCHES,
    ADMIN_MODULE_PRINTERS,
    ADMIN_MODULE_ARCHIVE,
    ADMIN_MODULE_TRAINING,
]


# =====================================================
# Cash & Printer
# =====================================================
CASH_DENOMINATIONS = [200, 100, 50, 20, 10, 5]

PRINTER_FIELDS = ["Total", "One Side", "Two Side", "Errors", "Jam"]

DEFAULT_PRINTERS = {
    "Kyocera 3010i": "192.168.1.120",
    "Xerox 7835": "192.168.1.65",
    "Kyocera P5031DN": "192.168.1.126",
}


# =====================================================
# Session State Keys
# =====================================================
SESSION_LOGGED_IN = "logged_in"
SESSION_USER = "user"
SESSION_ROLE = "role"
SESSION_BRANCH = "branch"
SESSION_SHIFT = "shift"

SESSION_OPEN_TOTAL = "t_open"
SESSION_CLOSE_TOTAL = "t_close"
SESSION_CASH_DIFF = "cash_diff"
SESSION_SYSTEM_SALES = "c_sys_sales"

SESSION_SHIFT_EXPENSES = "shift_expenses"
SESSION_PRINTER_START = "printer_start"
SESSION_PRINTER_END = "printer_end"
SESSION_PRINTER_DIFF = "printer_diff"

SESSION_OPAY_OPEN = "opay_open"
SESSION_OPAY_CLOSE = "opay_close"
SESSION_DEBIT_OPEN = "debit_open"
SESSION_DEBIT_CLOSE = "debit_close"
SESSION_NBE_OPEN = "nbe_open"
SESSION_NBE_CLOSE = "nbe_close"

SESSION_ACTIVE_DB = "_active_db"


# =====================================================
# Draft Prefixes
# =====================================================
DRAFT_PREFIXES = (
    "s_",
    "o_",
    "e_",
    "c_",
    "m_",
    "i_",
    "ks",
    "xs",
    "op",
    "u10",
    "v22",
    "ex",
    "kj",
    "xj",
    "dn",
    "k1",
    "k2",
    "x1",
    "x2",
)


# =====================================================
# Default User Schema
# =====================================================
DEFAULT_USER_SCHEMA = {
    "pass": "",
    "role": ROLE_USER,
    "full_name": "",
    "photo": None,
    "id_card": None,
    "phone": "",
    "email": "",
    "national_id": "",
    "address": "",
    "qualification": "",
    "hiring_date": DEFAULT_HIRING_DATE,
    "salary": 0.0,
    "bonus": [],
    "deductions": [],
    "overtime": [],
    "extra_leaves": [],
}


# =====================================================
# Default App Data Schema
# =====================================================
DEFAULT_APP_DATA = {
    "logo": None,
    "manager_phone": DEFAULT_MANAGER_PHONE,
    "branches": [],
    "expense_categories": [],
    "users": {
        "admin": {
            "pass": "admin123",
            "role": ROLE_ADMIN,
            "full_name": "Manager",
            "photo": None,
            "id_card": None,
            "phone": "",
            "email": "",
            "national_id": "",
            "address": "",
            "qualification": "",
            "hiring_date": DEFAULT_HIRING_DATE,
            "salary": 0.0,
            "bonus": [],
            "deductions": [],
            "overtime": [],
            "extra_leaves": [],
        }
    },
    "tasks": {
        TASK_OPENING: [],
        TASK_CLOSING: [],
        TASK_SOCIAL: [],
        TASK_INTERACTION: [],
    },
    "history": [],
    "drafts": {},
    "logs": [],
    "printers": DEFAULT_PRINTERS,
    "training_records": {},
}
