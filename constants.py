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
DEFAULT_BIRTH_DATE = "2000-01-01"
DEFAULT_MANAGER_PHONE = "+971522045638"


# =====================================================
# Roles
# =====================================================
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_EMPLOYEE = "employee"
ROLE_ACCOUNTS = "accounts"
ROLE_HR = "hr"
ROLE_CLEANER = "cleaner"
ROLE_GRAPHIC_DESIGNER = "graphic_designer"

ROLE_OPTIONS = [
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_EMPLOYEE,
    ROLE_ACCOUNTS,
    ROLE_HR,
    ROLE_CLEANER,
    ROLE_GRAPHIC_DESIGNER,
]

ROLE_LABELS = {
    ROLE_ADMIN: "Admin",
    ROLE_MANAGER: "Manager",
    ROLE_EMPLOYEE: "Customer Service",
    ROLE_ACCOUNTS: "Accounts",
    ROLE_HR: "HR",
    ROLE_CLEANER: "Cleaner",
    ROLE_GRAPHIC_DESIGNER: "Graphic Designer",
}


# =====================================================
# Legacy Compatibility
# =====================================================
ROLE_USER = ROLE_EMPLOYEE


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
# Shift Attendance Rules
# =====================================================
SHIFT_START_TIMES = {
    SHIFT_MORNING: {"hour": 8, "minute": 0},
    SHIFT_BETWEEN: {"hour": 12, "minute": 0},
    SHIFT_NIGHT: {"hour": 15, "minute": 0},
}

SHIFT_GRACE_MINUTES = 5
MAX_MONTHLY_LATE_WARNINGS = 3
MONTHLY_LATE_BLOCK_AT = 4


# =====================================================
# Task Categories
# =====================================================
TASK_OPENING = "opening"
TASK_CLOSING = "closing"
TASK_SOCIAL = "social"
TASK_INTERACTION = "interaction"
TASK_CLEANING = "cleaning"
TASK_DESIGN = "design"

TASK_CATEGORIES = [
    TASK_OPENING,
    TASK_CLOSING,
    TASK_SOCIAL,
    TASK_INTERACTION,
    TASK_CLEANING,
    TASK_DESIGN,
]

TASK_CATEGORY_LABELS = {
    TASK_OPENING: "Opening",
    TASK_CLOSING: "Closing",
    TASK_SOCIAL: "Social",
    TASK_INTERACTION: "Interaction",
    TASK_CLEANING: "Cleaning",
    TASK_DESIGN: "Design",
}


# =====================================================
# Role-Based Task Access
# =====================================================
ROLE_TASK_ACCESS = {
    ROLE_ADMIN: TASK_CATEGORIES,
    ROLE_MANAGER: [TASK_OPENING, TASK_CLOSING, TASK_SOCIAL, TASK_INTERACTION],
    ROLE_EMPLOYEE: [TASK_OPENING, TASK_CLOSING, TASK_SOCIAL, TASK_INTERACTION],
    ROLE_ACCOUNTS: [TASK_OPENING, TASK_CLOSING, TASK_INTERACTION],
    ROLE_HR: [TASK_INTERACTION],
    ROLE_CLEANER: [TASK_CLEANING],
    ROLE_GRAPHIC_DESIGNER: [TASK_DESIGN, TASK_SOCIAL, TASK_INTERACTION],
}


# =====================================================
# Default Tasks by Category
# =====================================================
DEFAULT_TASKS = {
    TASK_OPENING: [
        "Open branch and check lighting",
        "Check POS / system status",
        "Count opening cash",
        "Check internet connection",
        "Check printers status",
        "Prepare workstations",
    ],
    TASK_CLOSING: [
        "Count closing cash",
        "Review sales total",
        "Review expenses",
        "Check digital wallets",
        "Turn off devices safely",
        "Lock branch and secure keys",
    ],
    TASK_SOCIAL: [
        "Reply to pending social messages",
        "Upload daily social story",
        "Review customer comments",
    ],
    TASK_INTERACTION: [
        "Follow up with waiting customers",
        "Call customers for pickup confirmation",
        "Handle customer complaints professionally",
        "Confirm urgent orders status",
    ],
    TASK_CLEANING: [
        "Clean floors",
        "Clean reception desk",
        "Clean printer area",
        "Empty trash bins",
        "Sanitize customer seating area",
        "Check restroom cleanliness",
    ],
    TASK_DESIGN: [
        "Review pending design orders",
        "Prepare customer mockups",
        "Finalize print-ready files",
        "Check brand consistency",
        "Export final approved files",
        "Coordinate with printing team",
    ],
}


# =====================================================
# HR Record Types
# =====================================================
HR_BONUS = "bonus"
HR_DEDUCTIONS = "deductions"
HR_OVERTIME = "overtime"
HR_EXTRA_LEAVES = "extra_leaves"
HR_ADVANCES = "advances"
HR_LATE_PENALTIES = "late_penalties"
HR_ABSENCE_PENALTIES = "absence_penalties"

HR_RECORD_KEYS = [
    HR_BONUS,
    HR_DEDUCTIONS,
    HR_OVERTIME,
    HR_EXTRA_LEAVES,
    HR_ADVANCES,
    HR_LATE_PENALTIES,
    HR_ABSENCE_PENALTIES,
]

HR_RECORD_LABELS = {
    HR_BONUS: "Bonus",
    HR_DEDUCTIONS: "Deduction",
    HR_OVERTIME: "Overtime",
    HR_EXTRA_LEAVES: "Extra Leave",
    HR_ADVANCES: "Advance / Loan",
    HR_LATE_PENALTIES: "Late Penalty",
    HR_ABSENCE_PENALTIES: "Absence Penalty",
}

HR_FORM_TO_DB_KEY = {
    "Bonus": HR_BONUS,
    "Deduction": HR_DEDUCTIONS,
    "Overtime": HR_OVERTIME,
    "Extra Leave": HR_EXTRA_LEAVES,
    "Advance / Loan": HR_ADVANCES,
    "Late Penalty": HR_LATE_PENALTIES,
    "Absence Penalty": HR_ABSENCE_PENALTIES,
}


# =====================================================
# Payroll Entry UI Labels
# =====================================================
PAYROLL_ENTRY_OPTIONS = [
    "Bonus 🎁",
    "Deductions ⚠️",
    "Overtime ⏳",
    "Extra Leave 🏖️",
    "Advance / Loan 💵",
    "Late Penalty 🚨",
    "Absence Penalty 📅",
]

PAYROLL_ENTRY_KEY_MAP = {
    "Bonus 🎁": HR_BONUS,
    "Deductions ⚠️": HR_DEDUCTIONS,
    "Overtime ⏳": HR_OVERTIME,
    "Extra Leave 🏖️": HR_EXTRA_LEAVES,
    "Advance / Loan 💵": HR_ADVANCES,
    "Late Penalty 🚨": HR_LATE_PENALTIES,
    "Absence Penalty 📅": HR_ABSENCE_PENALTIES,
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
# Cash / Digital / Printer
# =====================================================
CASH_DENOMINATIONS = [200, 100, 50, 20, 10, 5]

PRINTER_FIELDS = ["Total", "One Side", "Two Side", "Errors", "Jam"]

DIGITAL_BALANCE_CHANNELS = [
    "opay",
    "nbe",
    "qnb",
    "fawry",
]

DEFAULT_PRINTERS = {
    "Kyocera 3010i": "192.168.1.120",
    "Xerox 7835": "192.168.1.65",
    "Kyocera P5031DN": "192.168.1.126",
}


# =====================================================
# Customer Debit
# =====================================================
CUSTOMER_DEBIT_FIELDS = [
    "customer_name",
    "customer_phone",
    "debt_amount",
]

DEFAULT_CUSTOMER_DEBT_ITEM = {
    "customer_name": "",
    "customer_phone": "",
    "debt_amount": 0.0,
}


# =====================================================
# Employee Finance Structure
# =====================================================
SALARY_COMPONENT_BASIC = "salary_basic"
SALARY_COMPONENT_TRANSPORT = "transport_allowance"
SALARY_COMPONENT_COMMUNICATION = "communication_allowance"
SALARY_COMPONENT_OTHER = "other_allowance"

SALARY_COMPONENT_KEYS = [
    SALARY_COMPONENT_BASIC,
    SALARY_COMPONENT_TRANSPORT,
    SALARY_COMPONENT_COMMUNICATION,
    SALARY_COMPONENT_OTHER,
]

SALARY_COMPONENT_LABELS = {
    SALARY_COMPONENT_BASIC: "Basic Salary",
    SALARY_COMPONENT_TRANSPORT: "Transport Allowance",
    SALARY_COMPONENT_COMMUNICATION: "Communication Allowance",
    SALARY_COMPONENT_OTHER: "Other Allowance",
}


# =====================================================
# Employee Payout Methods
# =====================================================
PAYOUT_METHOD_BANK = "bank"
PAYOUT_METHOD_WALLET = "wallet"
PAYOUT_METHOD_CASH = "cash"

PAYOUT_METHOD_OPTIONS = [
    PAYOUT_METHOD_BANK,
    PAYOUT_METHOD_WALLET,
    PAYOUT_METHOD_CASH,
]

PAYOUT_METHOD_LABELS = {
    PAYOUT_METHOD_BANK: "Bank Transfer",
    PAYOUT_METHOD_WALLET: "Wallet Transfer",
    PAYOUT_METHOD_CASH: "Cash",
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

SESSION_QNB_OPEN = "qnb_open"
SESSION_QNB_CLOSE = "qnb_close"

SESSION_FAWRY_OPEN = "fawry_open"
SESSION_FAWRY_CLOSE = "fawry_close"

SESSION_CUSTOMER_DEBTS = "customer_debts"

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
    "role": ROLE_EMPLOYEE,
    "full_name": "",
    "job_title": "",
    "photo": None,
    "id_card": None,
    "employee_code": "",
    "birth_date": DEFAULT_BIRTH_DATE,
    "phone": "",
    "email": "",
    "national_id": "",
    "address": "",
    "qualification": "",
    "hiring_date": DEFAULT_HIRING_DATE,
    "salary": 0.0,
    "salary_basic": 0.0,
    "transport_allowance": 0.0,
    "communication_allowance": 0.0,
    "other_allowance": 0.0,
    "bank_name": "",
    "bank_account_number": "",
    "wallet_number": "",
    "payout_method": PAYOUT_METHOD_BANK,
    "bonus": [],
    "deductions": [],
    "overtime": [],
    "extra_leaves": [],
    "advances": [],
    "late_penalties": [],
    "absence_penalties": [],
    "warnings": [],
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
            "job_title": "System Admin",
            "photo": None,
            "id_card": None,
            "employee_code": "ADMIN001",
            "birth_date": DEFAULT_BIRTH_DATE,
            "phone": "",
            "email": "",
            "national_id": "",
            "address": "",
            "qualification": "",
            "hiring_date": DEFAULT_HIRING_DATE,
            "salary": 0.0,
            "salary_basic": 0.0,
            "transport_allowance": 0.0,
            "communication_allowance": 0.0,
            "other_allowance": 0.0,
            "bank_name": "",
            "bank_account_number": "",
            "wallet_number": "",
            "payout_method": PAYOUT_METHOD_BANK,
            "bonus": [],
            "deductions": [],
            "overtime": [],
            "extra_leaves": [],
            "advances": [],
            "late_penalties": [],
            "absence_penalties": [],
            "warnings": [],
        }
    },
    "tasks": DEFAULT_TASKS,
    "history": [],
    "drafts": {},
    "logs": [],
    "printers": DEFAULT_PRINTERS,
    "training_records": {},
    "attendance_records": {},
    "late_tracking": {},
    "blocked_users": {},
}
