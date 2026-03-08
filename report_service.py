# =====================================================
# REPORT SERVICE
# Builds strict role-based report data and WhatsApp text
# =====================================================

from datetime import date

from auth_service import get_current_username
from role_service import get_report_type, get_normalized_current_role


def safe_float(value) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_text(value, default="-") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


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
        "opening_cash_breakdown": session_state.get("opening_cash_breakdown", {}),
        "closing_cash_breakdown": session_state.get("closing_cash_breakdown", {}),
        "opening_cash_text": build_cash_breakdown_text(session_state.get("opening_cash_breakdown", {})),
        "closing_cash_text": build_cash_breakdown_text(session_state.get("closing_cash_breakdown", {})),
        "opay_open": opay_open,
        "opay_close": opay_close,
        "opay_diff": opay_close - opay_open,
        "debit_open": debit_open,
        "debit_close": debit_close,
        "debit_diff": debit_close - debit_open,
        "nbe_open": nbe_open,
        "nbe_close": nbe_close,
        "nbe_diff": nbe_close - nbe_open,
        "printer_diff": session_state.get("printer_diff", {}),
        "printer_lines": build_printer_lines(session_state.get("printer_diff", {})),
        "social_notes": safe_text(session_state.get("social_notes", ""), "No Social Notes"),
        "interaction_notes": safe_text(session_state.get("interaction_notes", ""), "No Interaction Notes"),
        "special_notes": safe_text(session_state.get("special_notes", ""), "No Special Notes"),
    }


def build_role_report_data(db: dict, session_state) -> dict:
    data = build_base_report_data(db, session_state)
    report_type = data["report_type"]

    if report_type == "financial":
        data["visible_sections"] = ["summary", "cash_breakdown", "digital", "expenses"]
    elif report_type == "hr":
        data["visible_sections"] = ["identity", "interaction_notes", "special_notes"]
    elif report_type == "cleaning":
        data["visible_sections"] = ["identity", "special_notes"]
    elif report_type == "design":
        data["visible_sections"] = ["identity", "social_notes", "special_notes"]
    elif report_type == "full":
        data["visible_sections"] = [
            "summary",
            "cash_breakdown",
            "digital",
            "expenses",
            "interaction_notes",
            "social_notes",
            "special_notes",
            "printers",
        ]
    else:
        data["visible_sections"] = ["summary", "interaction_notes", "social_notes", "special_notes"]

    return data


def build_whatsapp_text(db: dict, session_state) -> str:
    report = build_role_report_data(db, session_state)
    report_type = report["report_type"]

    header = (
        f"NMS {report_type.upper()} REPORT\n"
        f"Date: {report['date']}\n"
        f"Branch: {report['branch']}\n"
        f"Shift: {report['shift']}\n"
        f"Staff: {report['staff']}\n"
        f"Role: {report['role']}\n"
    )

    if report_type == "financial":
        body = f"""
SALES
Total System Sales: {report['sales']:,.2f}

OPENING CASH
{report['opening_cash_text']}
Total Opening Cash: {report['t_open']:,.2f}

CLOSING CASH
{report['closing_cash_text']}
Total Closing Cash: {report['t_close']:,.2f}

DIGITAL
Opay Diff: {report['opay_diff']:,.2f}
Debit Diff: {report['debit_diff']:,.2f}
NBE Diff: {report['nbe_diff']:,.2f}

EXPENSES
Total Expenses: {report['total_expenses']:,.2f}
{report['expense_lines']}

CASH DIFFERENCE
{report['cash_diff']:,.2f}
"""
    elif report_type == "hr":
        body = f"""
HR REPORT

INTERACTION NOTES
{report['interaction_notes']}

HR NOTES
{report['special_notes']}
"""
    elif report_type == "cleaning":
        body = f"""
CLEANING REPORT

CLEANING NOTES
{report['special_notes']}
"""
    elif report_type == "design":
        body = f"""
DESIGN REPORT

SOCIAL NOTES
{report['social_notes']}

DESIGN NOTES
{report['special_notes']}
"""
    elif report_type == "full":
        body = f"""
FULL REPORT

SALES
Total System Sales: {report['sales']:,.2f}

OPENING CASH
{report['opening_cash_text']}

CLOSING CASH
{report['closing_cash_text']}

EXPENSES
Total Expenses: {report['total_expenses']:,.2f}
{report['expense_lines']}

INTERACTION NOTES
{report['interaction_notes']}

SOCIAL NOTES
{report['social_notes']}

SPECIAL NOTES
{report['special_notes']}

PRINTERS
{report['printer_lines']}

CASH DIFFERENCE
{report['cash_diff']:,.2f}
"""
    else:
        body = f"""
OPERATIONS REPORT

SALES
{report['sales']:,.2f}

EXPENSES
{report['total_expenses']:,.2f}

CASH DIFFERENCE
{report['cash_diff']:,.2f}

INTERACTION NOTES
{report['interaction_notes']}

SOCIAL NOTES
{report['social_notes']}

SPECIAL NOTES
{report['special_notes']}
"""

    return (header + "\n" + body + "\nGenerated by NMS System").strip()[:3500]
