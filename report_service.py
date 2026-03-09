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

    expenses_list = session_state.get("shift_expenses", [])
    total_expenses = calculate_total_expenses(expenses_list)

    opay_open = safe_float(session_state.get("opay_open", 0))
    opay_close = safe_float(session_state.get("opay_close", 0))
    debit_open = safe_float(session_state.get("debit_open", 0))
    debit_close = safe_float(session_state.get("debit_close", 0))
    nbe_open = safe_float(session_state.get("nbe_open", 0))
    nbe_close = safe_float(session_state.get("nbe_close", 0))

    opening_cash_breakdown = session_state.get("opening_cash_breakdown", {})
    closing_cash_breakdown = session_state.get("closing_cash_breakdown", {})
    printer_diff = session_state.get("printer_diff", {})

    return {
        "date": str(date.today()),
        "branch": session_state.get("branch", "-"),
        "shift": session_state.get("shift", "-"),
        "staff": user_data["full_name"],
        "staff_username": user_data["username"],
        "role": user_data["role"],
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
        "printer_diff": printer_diff,
        "printer_lines": build_printer_lines(printer_diff),
        "social_notes": safe_text(session_state.get("social_notes", ""), "No Social Notes"),
        "interaction_notes": safe_text(session_state.get("interaction_notes", ""), "No Interaction Notes"),
        "special_notes": safe_text(session_state.get("special_notes", ""), "No Special Notes"),
    }


# =====================================================
# Visible Sections
# =====================================================
def get_visible_sections(report_type: str) -> list[str]:
    if report_type == "financial":
        return ["identity", "summary", "cash_breakdown", "digital", "expenses"]
    if report_type == "hr":
        return ["identity", "interaction_notes", "special_notes"]
    if report_type == "cleaning":
        return ["identity", "special_notes"]
    if report_type == "design":
        return ["identity", "social_notes", "special_notes"]
    if report_type == "full":
        return [
            "identity",
            "summary",
            "cash_breakdown",
            "digital",
            "expenses",
            "interaction_notes",
            "social_notes",
            "special_notes",
            "printers",
        ]
    return ["identity", "summary", "interaction_notes", "social_notes", "special_notes"]


def build_role_report_data(db: dict, session_state) -> dict:
    data = build_base_report_data(db, session_state)
    data["visible_sections"] = get_visible_sections(data["report_type"])
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
            "DIGITAL",
            f"Opay Diff: {report['opay_diff']:,.2f}",
            f"Debit Diff: {report['debit_diff']:,.2f}",
            f"NBE Diff: {report['nbe_diff']:,.2f}",
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
    if section_name == "expenses":
        return build_expenses_section(report)
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
