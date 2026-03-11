# =====================================================
# REPORT SERVICE
# Builds strict role-based report data and WhatsApp text
# =====================================================

from datetime import date

from auth_service import get_current_username
from role_service import get_normalized_current_role, get_report_type


# =====================================================
# Generic Helpers
# =====================================================
def safe_float(value) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_text(value, default="-") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def join_non_empty_sections(sections: list[str]) -> str:
    cleaned = [section.strip() for section in sections if str(section).strip()]
    return "\n\n".join(cleaned)


# =====================================================
# Role-based task visibility helpers
# =====================================================
def can_include_opening_tasks_for_role(role_value: str) -> bool:
    return role_value in ["admin", "manager", "accounts"]


def can_include_closing_tasks_for_role(role_value: str) -> bool:
    return role_value in ["admin", "manager", "accounts"]


def can_include_interaction_tasks_for_role(role_value: str) -> bool:
    return role_value in ["admin", "manager", "hr", "employee"]


def can_include_social_tasks_for_role(role_value: str) -> bool:
    return role_value in ["admin", "manager", "graphic_designer", "employee"]


def can_include_cleaning_tasks_for_role(role_value: str) -> bool:
    return role_value in ["admin", "cleaner"]


def can_include_design_tasks_for_role(role_value: str) -> bool:
    return role_value in ["admin", "graphic_designer"]


# =====================================================
# Task Helpers
# =====================================================
def extract_task_status(task_list: list, key_prefix: str, session_state) -> dict:
    completed = []
    pending = []

    for idx, task in enumerate(task_list or []):
        key = f"{key_prefix}_{idx}_{task}"
        is_done = bool(session_state.get(key, False))

        if is_done:
            completed.append(task)
        else:
            pending.append(task)

    return {
        "completed": completed,
        "pending": pending,
    }


def build_task_lines(title: str, completed: list, pending: list) -> str:
    lines = [title]

    if completed:
        lines.append("Completed Tasks:")
        lines.extend([f"- {task}" for task in completed])
    else:
        lines.append("Completed Tasks: None")

    lines.append("")

    if pending:
        lines.append("Pending Tasks:")
        lines.extend([f"- {task}" for task in pending])
    else:
        lines.append("Pending Tasks: None")

    return "\n".join(lines)


# =====================================================
# Data Builders
# =====================================================
def calculate_total_expenses(expenses: list) -> float:
    return sum(safe_float(item.get("amount", 0)) for item in (expenses or []))


def build_expense_lines(expenses: list) -> str:
    if not expenses:
        return "No Expenses Recorded"

    return "\n".join(
        f"- {item.get('type', 'Unknown')} : {safe_float(item.get('amount', 0)):,.2f}"
        for item in expenses
    )


def build_cash_breakdown_text(breakdown: dict) -> str:
    if not breakdown:
        return "No Cash Breakdown"

    ordered = ["200", "100", "50", "20", "10", "5", "coins"]
    lines = []

    for key in ordered:
        if key not in breakdown:
            continue

        label = "Coins" if key == "coins" else f"{key} LE"
        qty = breakdown[key].get("qty", 0)
        total = safe_float(breakdown[key].get("total", 0))
        lines.append(f"- {label}: {qty} = {total:,.2f}")

    return "\n".join(lines) if lines else "No Cash Breakdown"


def build_printer_lines(printer_diff: dict) -> str:
    if not printer_diff:
        return "No Printer Data"

    sections = []
    for printer_name, values in printer_diff.items():
        sections.append(
            "\n".join(
                [
                    f"Printer: {printer_name}",
                    f"Used: {values.get('used', 0)}",
                    f"Jam: {values.get('jam', 0)}",
                    f"1-Side: {values.get('1s', 0)}",
                    f"2-Side: {values.get('2s', 0)}",
                ]
            )
        )

    return "\n\n".join(sections)


def build_customer_debts_lines(customer_debts: list) -> str:
    if not customer_debts:
        return "No Customer Debts"

    lines = []
    for item in customer_debts:
        lines.append(
            f"- {safe_text(item.get('customer_name', '-'))}"
            f" | {safe_text(item.get('customer_phone', '-'))}"
            f" | {safe_float(item.get('debt_amount', 0)):,.2f} LE"
        )

    return "\n".join(lines)


def calculate_total_customer_debts(customer_debts: list) -> float:
    return sum(safe_float(item.get("debt_amount", 0)) for item in (customer_debts or []))


def get_user_display_data(db: dict) -> dict:
    username = get_current_username() or "-"
    user_record = db.get("users", {}).get(username, {})
    normalized_role = get_normalized_current_role()

    return {
        "username": username,
        "full_name": user_record.get("full_name") or username,
        "role": normalized_role,
        "job_title": user_record.get("job_title", ""),
    }


def build_base_report_data(db: dict, session_state) -> dict:
    user_data = get_user_display_data(db)
    current_role = user_data["role"]

    expenses_list = session_state.get("shift_expenses", [])
    total_expenses = calculate_total_expenses(expenses_list)

    customer_debts = session_state.get("customer_debts", [])
    total_customer_debts = calculate_total_customer_debts(customer_debts)

    opay_open = safe_float(session_state.get("opay_open", 0))
    opay_close = safe_float(session_state.get("opay_close", 0))

    debit_open = safe_float(session_state.get("debit_open", 0))
    debit_close = safe_float(session_state.get("debit_close", 0))

    nbe_open = safe_float(session_state.get("nbe_open", 0))
    nbe_close = safe_float(session_state.get("nbe_close", 0))

    qnb_open = safe_float(session_state.get("qnb_open", 0))
    qnb_close = safe_float(session_state.get("qnb_close", 0))

    fawry_open = safe_float(session_state.get("fawry_open", 0))
    fawry_close = safe_float(session_state.get("fawry_close", 0))

    opening_cash_breakdown = session_state.get("opening_cash_breakdown", {})
    closing_cash_breakdown = session_state.get("closing_cash_breakdown", {})
    printer_diff = session_state.get("printer_diff", {})

    opening_tasks = (
        db.get("tasks", {}).get("opening", [])
        if can_include_opening_tasks_for_role(current_role)
        else []
    )
    closing_tasks = (
        db.get("tasks", {}).get("closing", [])
        if can_include_closing_tasks_for_role(current_role)
        else []
    )
    interaction_tasks = (
        db.get("tasks", {}).get("interaction", [])
        if can_include_interaction_tasks_for_role(current_role)
        else []
    )
    social_tasks = (
        db.get("tasks", {}).get("social", [])
        if can_include_social_tasks_for_role(current_role)
        else []
    )
    cleaning_tasks = (
        db.get("tasks", {}).get("cleaning", [])
        if can_include_cleaning_tasks_for_role(current_role)
        else []
    )
    design_tasks = (
        db.get("tasks", {}).get("design", [])
        if can_include_design_tasks_for_role(current_role)
        else []
    )

    opening_status = extract_task_status(opening_tasks, "open_task", session_state)
    closing_status = extract_task_status(closing_tasks, "close_task", session_state)
    interaction_status = extract_task_status(interaction_tasks, "interaction_task", session_state)
    social_status = extract_task_status(social_tasks, "social_task", session_state)
    cleaning_status = extract_task_status(cleaning_tasks, "cleaning_task", session_state)
    design_status = extract_task_status(design_tasks, "design_task", session_state)

    return {
        "date": str(date.today()),
        "branch": session_state.get("branch", "-"),
        "shift": session_state.get("shift", "-"),
        "staff": user_data["full_name"],
        "staff_username": user_data["username"],
        "role": current_role,
        "job_title": user_data["job_title"],
        "report_type": get_report_type(),
        "sales": safe_float(session_state.get("c_sys_sales", 0)),
        "expenses_list": expenses_list,
        "total_expenses": total_expenses,
        "expense_lines": build_expense_lines(expenses_list),
        "cash_diff": safe_float(session_state.get("cash_diff", 0)),
        "t_open": safe_float(session_state.get("t_open", 0)),
        "t_close": safe_float(session_state.get("t_close", 0)),
        "opening_cash_breakdown": opening_cash_breakdown,
        "closing_cash_breakdown": closing_cash_breakdown,
        "opening_cash_text": build_cash_breakdown_text(opening_cash_breakdown),
        "closing_cash_text": build_cash_breakdown_text(closing_cash_breakdown),
        "opay_open": opay_open,
        "opay_close": opay_close,
        "opay_diff": opay_close - opay_open,
        "debit_open": debit_open,
        "debit_close": debit_close,
        "debit_diff": debit_close - debit_open,
        "nbe_open": nbe_open,
        "nbe_close": nbe_close,
        "nbe_diff": nbe_close - nbe_open,
        "qnb_open": qnb_open,
        "qnb_close": qnb_close,
        "qnb_diff": qnb_close - qnb_open,
        "fawry_open": fawry_open,
        "fawry_close": fawry_close,
        "fawry_diff": fawry_close - fawry_open,
        "customer_debts": customer_debts,
        "customer_debts_lines": build_customer_debts_lines(customer_debts),
        "total_customer_debts": total_customer_debts,
        "printer_diff": printer_diff,
        "printer_lines": build_printer_lines(printer_diff),
        "social_notes": safe_text(session_state.get("social_notes", ""), "No Social Notes"),
        "interaction_notes": safe_text(session_state.get("interaction_notes", ""), "No Interaction Notes"),
        "special_notes": safe_text(session_state.get("special_notes", ""), "No Special Notes"),
        "opening_tasks_completed": opening_status["completed"],
        "opening_tasks_pending": opening_status["pending"],
        "closing_tasks_completed": closing_status["completed"],
        "closing_tasks_pending": closing_status["pending"],
        "interaction_tasks_completed": interaction_status["completed"],
        "interaction_tasks_pending": interaction_status["pending"],
        "social_tasks_completed": social_status["completed"],
        "social_tasks_pending": social_status["pending"],
        "cleaning_tasks_completed": cleaning_status["completed"],
        "cleaning_tasks_pending": cleaning_status["pending"],
        "design_tasks_completed": design_status["completed"],
        "design_tasks_pending": design_status["pending"],
    }


# =====================================================
# Pending tasks warning
# =====================================================
def get_all_pending_tasks(report: dict) -> list[str]:
    pending_sections = [
        ("Opening", report.get("opening_tasks_pending", [])),
        ("Closing", report.get("closing_tasks_pending", [])),
        ("Interaction", report.get("interaction_tasks_pending", [])),
        ("Social", report.get("social_tasks_pending", [])),
        ("Cleaning", report.get("cleaning_tasks_pending", [])),
        ("Design", report.get("design_tasks_pending", [])),
    ]

    pending_items = []
    for section_name, tasks in pending_sections:
        for task in tasks or []:
            pending_items.append(f"{section_name}: {task}")

    return pending_items


def has_pending_tasks(report: dict) -> bool:
    return len(get_all_pending_tasks(report)) > 0


def build_pending_tasks_warning(report: dict) -> str:
    pending_items = get_all_pending_tasks(report)

    if not pending_items:
        return ""

    lines = [
        "⚠️ يوجد مهام غير مكتملة في هذا الشيفت.",
        "يجب إتمام كل المهام المسندة إليك لتجنب أي خصومات.",
        "",
        "Pending Tasks:",
    ]
    lines.extend([f"- {item}" for item in pending_items])

    return "\n".join(lines)


# =====================================================
# Visible Sections
# =====================================================
def get_visible_sections(report_type: str) -> list[str]:
    if report_type == "financial":
        return [
            "identity",
            "summary",
            "cash_breakdown",
            "digital",
            "customer_debts",
            "expenses",
            "tasks",
            "printers",
        ]

    if report_type == "hr":
        return ["identity", "interaction_notes", "special_notes", "tasks"]

    if report_type == "cleaning":
        return ["identity", "special_notes", "tasks"]

    if report_type == "design":
        return ["identity", "social_notes", "special_notes", "tasks"]

    if report_type == "customer_service":
        return [
            "identity",
            "summary",
            "cash_breakdown",
            "digital",
            "customer_debts",
            "expenses",
            "tasks",
            "interaction_notes",
            "social_notes",
            "special_notes",
            "printers",
        ]

    if report_type == "full":
        return [
            "identity",
            "summary",
            "cash_breakdown",
            "digital",
            "customer_debts",
            "expenses",
            "tasks",
            "interaction_notes",
            "social_notes",
            "special_notes",
            "printers",
        ]

    return [
        "identity",
        "summary",
        "cash_breakdown",
        "digital",
        "customer_debts",
        "expenses",
        "tasks",
        "interaction_notes",
        "social_notes",
        "special_notes",
        "printers",
    ]


def build_role_report_data(db: dict, session_state) -> dict:
    data = build_base_report_data(db, session_state)
    data["visible_sections"] = get_visible_sections(data["report_type"])
    data["has_pending_tasks"] = has_pending_tasks(data)
    data["pending_tasks_warning"] = build_pending_tasks_warning(data)
    return data


# =====================================================
# WhatsApp Section Builders
# =====================================================
def build_identity_section(report: dict) -> str:
    return "\n".join(
        [
            f"Date: {report['date']}",
            f"Branch: {report['branch']}",
            f"Shift: {report['shift']}",
            f"Staff: {report['staff']}",
            f"Role: {report['role']}",
            f"Job Title: {report['job_title'] or '-'}",
        ]
    )


def build_summary_section(report: dict) -> str:
    return "\n".join(
        [
            "SALES",
            f"Total System Sales: {report['sales']:,.2f}",
            "",
            "CASH DIFFERENCE",
            f"{report['cash_diff']:,.2f}",
        ]
    )


def build_cash_breakdown_section(report: dict) -> str:
    return "\n".join(
        [
            "OPENING CASH",
            report["opening_cash_text"],
            f"Total Opening Cash: {report['t_open']:,.2f}",
            "",
            "CLOSING CASH",
            report["closing_cash_text"],
            f"Total Closing Cash: {report['t_close']:,.2f}",
        ]
    )


def build_digital_section(report: dict) -> str:
    return "\n".join(
        [
            "DIGITAL BALANCES",
            "",
            "OPAY",
            f"Open: {report['opay_open']:,.2f}",
            f"Close: {report['opay_close']:,.2f}",
            f"Diff: {report['opay_diff']:,.2f}",
            "",
            "CUSTOMER DEBIT",
            f"Open: {report['debit_open']:,.2f}",
            f"Close: {report['debit_close']:,.2f}",
            f"Diff: {report['debit_diff']:,.2f}",
            "",
            "NBE",
            f"Open: {report['nbe_open']:,.2f}",
            f"Close: {report['nbe_close']:,.2f}",
            f"Diff: {report['nbe_diff']:,.2f}",
            "",
            "QNB / INSTAPAY",
            f"Open: {report['qnb_open']:,.2f}",
            f"Close: {report['qnb_close']:,.2f}",
            f"Diff: {report['qnb_diff']:,.2f}",
            "",
            "FAWRY",
            f"Open: {report['fawry_open']:,.2f}",
            f"Close: {report['fawry_close']:,.2f}",
            f"Diff: {report['fawry_diff']:,.2f}",
        ]
    )


def build_customer_debts_section(report: dict) -> str:
    return "\n".join(
        [
            "CUSTOMER DEBTS DETAILS",
            f"Total Customer Debts: {report['total_customer_debts']:,.2f}",
            report["customer_debts_lines"],
        ]
    )


def build_expenses_section(report: dict) -> str:
    return "\n".join(
        [
            "EXPENSES",
            f"Total Expenses: {report['total_expenses']:,.2f}",
            report["expense_lines"],
        ]
    )


def build_tasks_section(report: dict) -> str:
    sections = []

    if report.get("opening_tasks_completed") or report.get("opening_tasks_pending"):
        sections.append(
            build_task_lines(
                "OPENING TASKS",
                report.get("opening_tasks_completed", []),
                report.get("opening_tasks_pending", []),
            )
        )

    if report.get("closing_tasks_completed") or report.get("closing_tasks_pending"):
        sections.append(
            build_task_lines(
                "CLOSING TASKS",
                report.get("closing_tasks_completed", []),
                report.get("closing_tasks_pending", []),
            )
        )

    if report.get("interaction_tasks_completed") or report.get("interaction_tasks_pending"):
        sections.append(
            build_task_lines(
                "INTERACTION TASKS",
                report.get("interaction_tasks_completed", []),
                report.get("interaction_tasks_pending", []),
            )
        )

    if report.get("social_tasks_completed") or report.get("social_tasks_pending"):
        sections.append(
            build_task_lines(
                "SOCIAL TASKS",
                report.get("social_tasks_completed", []),
                report.get("social_tasks_pending", []),
            )
        )

    if report.get("cleaning_tasks_completed") or report.get("cleaning_tasks_pending"):
        sections.append(
            build_task_lines(
                "CLEANING TASKS",
                report.get("cleaning_tasks_completed", []),
                report.get("cleaning_tasks_pending", []),
            )
        )

    if report.get("design_tasks_completed") or report.get("design_tasks_pending"):
        sections.append(
            build_task_lines(
                "DESIGN TASKS",
                report.get("design_tasks_completed", []),
                report.get("design_tasks_pending", []),
            )
        )

    if not sections:
        return "TASKS\nNo Tasks Found"

    return join_non_empty_sections(sections)


def build_interaction_notes_section(report: dict) -> str:
    return "\n".join(
        [
            "INTERACTION NOTES",
            report["interaction_notes"],
        ]
    )


def build_social_notes_section(report: dict) -> str:
    return "\n".join(
        [
            "SOCIAL NOTES",
            report["social_notes"],
        ]
    )


def build_special_notes_section(report: dict) -> str:
    report_type = report.get("report_type", "")

    if report_type == "hr":
        title = "HR NOTES"
    elif report_type == "cleaning":
        title = "CLEANING NOTES"
    elif report_type == "design":
        title = "DESIGN NOTES"
    else:
        title = "SPECIAL NOTES"

    return "\n".join(
        [
            title,
            report["special_notes"],
        ]
    )


def build_printers_section(report: dict) -> str:
    return "\n".join(
        [
            "PRINTERS",
            report["printer_lines"],
        ]
    )


def build_section_text(section_name: str, report: dict) -> str:
    if section_name == "identity":
        return build_identity_section(report)
    if section_name == "summary":
        return build_summary_section(report)
    if section_name == "cash_breakdown":
        return build_cash_breakdown_section(report)
    if section_name == "digital":
        return build_digital_section(report)
    if section_name == "customer_debts":
        return build_customer_debts_section(report)
    if section_name == "expenses":
        return build_expenses_section(report)
    if section_name == "tasks":
        return build_tasks_section(report)
    if section_name == "interaction_notes":
        return build_interaction_notes_section(report)
    if section_name == "social_notes":
        return build_social_notes_section(report)
    if section_name == "special_notes":
        return build_special_notes_section(report)
    if section_name == "printers":
        return build_printers_section(report)
    return ""


# =====================================================
# WhatsApp
# =====================================================
def build_whatsapp_text(db: dict, session_state) -> str:
    report = build_role_report_data(db, session_state)
    report_type = report["report_type"]

    title = f"NMS {report_type.upper()} REPORT"

    visible_sections = report.get("visible_sections", [])
    section_blocks = [build_section_text(section_name, report) for section_name in visible_sections]

    full_text = join_non_empty_sections(
        [
            title,
            *section_blocks,
            "Generated by NMS System",
        ]
    )

    return full_text.strip()[:3500]
