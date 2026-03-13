import io
import base64

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from database import load_db


# =====================================================
# Helpers
# =====================================================
def _safe_image_from_base64(image_b64: str, width: float, height: float):
    if not image_b64:
        return ""

    try:
        image_bytes = base64.b64decode(image_b64)
        return Image(io.BytesIO(image_bytes), width=width, height=height)
    except Exception:
        return ""


def _safe_number(value) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _safe_text(value, default="-") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _to_paragraph_text(value) -> str:
    return _safe_text(value).replace("\n", "<br/>")


def _has_section(visible_sections: list | None, section_name: str) -> bool:
    if not visible_sections:
        return True
    return section_name in visible_sections


def _normalize_report_type(report_type: str) -> str:
    return str(report_type or "").strip().lower()


def _get_special_notes_title(report_type: str) -> str:
    normalized = _normalize_report_type(report_type)

    if normalized == "hr":
        return "HR Notes"
    if normalized == "cleaning":
        return "Cleaning Notes"
    if normalized == "design":
        return "Design Notes"
    if normalized in ["moderator", "moderation"]:
        return "Moderation Notes"
    return "Special Notes"


def _has_task_data(completed: list | None, pending: list | None) -> bool:
    return bool(completed or pending)


# =====================================================
# Builders
# =====================================================
def _build_header(
    branch: str,
    staff_name: str,
    date_str: str,
    shift: str,
    staff_role: str,
    job_title: str,
    report_type: str,
    styles,
    db: dict,
):
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        alignment=1,
        spaceAfter=10,
        textColor=colors.darkblue,
    )

    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=11,
        alignment=1,
        spaceAfter=18,
    )

    logo_img = _safe_image_from_base64(db.get("logo", ""), 1.2 * inch, 1.2 * inch)

    staff_photo_b64 = ""
    for _, user_data in db.get("users", {}).items():
        if user_data.get("full_name") == staff_name:
            staff_photo_b64 = user_data.get("photo", "")
            break

    staff_img = _safe_image_from_base64(staff_photo_b64, 1.0 * inch, 1.0 * inch)

    report_title = f"NMS {(_safe_text(report_type, 'operations')).upper()} REPORT"

    header_table = Table(
        [[logo_img, Paragraph(f"<b>{report_title}</b><br/>{_safe_text(branch)}", title_style), staff_img]],
        colWidths=[2 * inch, 6 * inch, 2 * inch],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    meta = Paragraph(
        f"Date: {_safe_text(date_str)} | Staff: {_safe_text(staff_name)} | "
        f"Role: {_safe_text(staff_role)} | Job Title: {_safe_text(job_title)} | Shift: {_safe_text(shift)}",
        sub_style,
    )

    return [header_table, Spacer(1, 10), meta, Spacer(1, 18)]


def _build_identity_block(styles, staff_name, staff_role, job_title, branch, shift, date_str):
    info_text = (
        f"Staff: {_safe_text(staff_name)}<br/>"
        f"Role: {_safe_text(staff_role)}<br/>"
        f"Job Title: {_safe_text(job_title)}<br/>"
        f"Branch: {_safe_text(branch)}<br/>"
        f"Shift: {_safe_text(shift)}<br/>"
        f"Date: {_safe_text(date_str)}"
    )

    table = Table(
        [["Identity Information"], [Paragraph(info_text, styles["Normal"])]],
        colWidths=[9 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2F8")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    return [Paragraph("Identity", styles["Heading2"]), Spacer(1, 10), table, Spacer(1, 18)]


def _build_info_table(styles, sales, expenses, diff, opening_cash, closing_cash):
    table_data = [
        ["Item", "Value"],
        ["Total Sales", f"{_safe_number(sales):,.2f} LE"],
        ["Total Expenses", f"{_safe_number(expenses):,.2f} LE"],
        ["Opening Cash", f"{_safe_number(opening_cash):,.2f} LE"],
        ["Closing Cash", f"{_safe_number(closing_cash):,.2f} LE"],
        ["Cash Difference", f"{_safe_number(diff):,.2f} LE"],
    ]

    table = Table(table_data, colWidths=[4.5 * inch, 4.5 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return [Paragraph("Shift Summary", styles["Heading2"]), Spacer(1, 10), table, Spacer(1, 18)]


def _build_digital_table(
    styles,
    opay_open,
    opay_close,
    opay_diff,
    debit_open,
    debit_close,
    debit_diff,
    nbe_open,
    nbe_close,
    nbe_diff,
    qnb_open,
    qnb_close,
    qnb_diff,
    fawry_open,
    fawry_close,
    fawry_diff,
):
    table_data = [
        ["Channel", "Open", "Close", "Diff"],
        [
            "Opay",
            f"{_safe_number(opay_open):,.2f} LE",
            f"{_safe_number(opay_close):,.2f} LE",
            f"{_safe_number(opay_diff):,.2f} LE",
        ],
        [
            "Customer Debit",
            f"{_safe_number(debit_open):,.2f} LE",
            f"{_safe_number(debit_close):,.2f} LE",
            f"{_safe_number(debit_diff):,.2f} LE",
        ],
        [
            "NBE Wallet",
            f"{_safe_number(nbe_open):,.2f} LE",
            f"{_safe_number(nbe_close):,.2f} LE",
            f"{_safe_number(nbe_diff):,.2f} LE",
        ],
        [
            "QNB / InstaPay",
            f"{_safe_number(qnb_open):,.2f} LE",
            f"{_safe_number(qnb_close):,.2f} LE",
            f"{_safe_number(qnb_diff):,.2f} LE",
        ],
        [
            "Fawry",
            f"{_safe_number(fawry_open):,.2f} LE",
            f"{_safe_number(fawry_close):,.2f} LE",
            f"{_safe_number(fawry_diff):,.2f} LE",
        ],
    ]

    table = Table(
        table_data,
        colWidths=[3 * inch, 2 * inch, 2 * inch, 2 * inch],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return [Paragraph("Digital Balances", styles["Heading2"]), Spacer(1, 10), table, Spacer(1, 18)]


def _build_customer_debts_table(styles, customer_debts: list, total_customer_debts: float):
    table_data = [["Customer Name", "Phone", "Debt Amount"]]

    if customer_debts:
        for item in customer_debts:
            table_data.append(
                [
                    _safe_text(item.get("customer_name", "-")),
                    _safe_text(item.get("customer_phone", "-")),
                    f"{_safe_number(item.get('debt_amount', 0)):,.2f} LE",
                ]
            )
    else:
        table_data.append(["No Customer Debts", "-", "-"])

    table = Table(table_data, colWidths=[4 * inch, 2.5 * inch, 2.5 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FDEBD0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    total_para = Paragraph(
        f"<b>Total Customer Debts:</b> {_safe_number(total_customer_debts):,.2f} LE",
        styles["Normal"],
    )

    return [
        Paragraph("Customer Debts", styles["Heading2"]),
        Spacer(1, 10),
        table,
        Spacer(1, 8),
        total_para,
        Spacer(1, 18),
    ]


def _build_expenses_table(styles, expenses_list: list, exp_note: str):
    table_data = [["Expense Type", "Amount"]]

    if expenses_list:
        for item in expenses_list:
            table_data.append(
                [
                    _safe_text(item.get("type", "Unknown")),
                    f"{_safe_number(item.get('amount', 0)):,.2f} LE",
                ]
            )
    else:
        table_data.append(["No Expenses Recorded", "-"])

    table = Table(table_data, colWidths=[6 * inch, 3 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.orange),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    note_para = Paragraph(_to_paragraph_text(exp_note), styles["Normal"])

    return [
        Paragraph("Expenses Details", styles["Heading2"]),
        Spacer(1, 10),
        table,
        Spacer(1, 8),
        Paragraph("<b>Expense Notes</b>", styles["Normal"]),
        Spacer(1, 4),
        note_para,
        Spacer(1, 18),
    ]


def _build_cash_breakdown_table(styles, title: str, breakdown_text: str):
    table_data = [
        ["Cash Breakdown"],
        [Paragraph(_to_paragraph_text(breakdown_text), styles["Normal"])],
    ]

    table = Table(table_data, colWidths=[9 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    return [Paragraph(title, styles["Heading2"]), Spacer(1, 10), table, Spacer(1, 18)]


def _build_notes_section(styles, title: str, value: str):
    return [
        Paragraph(title, styles["Heading2"]),
        Spacer(1, 6),
        Paragraph(_to_paragraph_text(value), styles["Normal"]),
        Spacer(1, 16),
    ]


def _build_printer_table(printer_diff: dict, styles):
    table_data = [["Printer", "Used", "Jam", "1-Side", "2-Side"]]

    if printer_diff:
        for printer_name, values in printer_diff.items():
            table_data.append(
                [
                    str(printer_name),
                    values.get("used", 0),
                    values.get("jam", 0),
                    values.get("1s", 0),
                    values.get("2s", 0),
                ]
            )
    else:
        table_data.append(["No Printer Data", "-", "-", "-", "-"])

    table = Table(
        table_data,
        colWidths=[3 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return [Paragraph("Printer Analysis", styles["Heading2"]), Spacer(1, 10), table, Spacer(1, 20)]


def _build_task_status_table(styles, title: str, completed: list, pending: list):
    rows = [["Status", "Task"]]

    if completed:
        for task in completed:
            rows.append(["Completed", _safe_text(task)])

    if pending:
        for task in pending:
            rows.append(["Pending", _safe_text(task)])

    if len(rows) == 1:
        rows.append(["-", "No Tasks"])

    table = Table(rows, colWidths=[2 * inch, 7 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return [Paragraph(title, styles["Heading2"]), Spacer(1, 8), table, Spacer(1, 16)]


# =====================================================
# Main PDF Generator
# =====================================================
def create_downloadable_pdf(
    branch,
    staff_name,
    date_str,
    sales,
    expenses,
    exp_note,
    diff,
    printer_diff,
    opay_move,
    debit_v22,
    shift="-",
    staff_role="-",
    opening_cash=0,
    closing_cash=0,
    opening_cash_text="No Cash Breakdown",
    closing_cash_text="No Cash Breakdown",
    nbe_move=0,
    social_notes="",
    interaction_notes="",
    special_notes="",
    expenses_list=None,
    report_type="operations",
    visible_sections=None,
    job_title="",
    opay_open=0,
    opay_close=0,
    debit_open=0,
    debit_close=0,
    nbe_open=0,
    nbe_close=0,
    qnb_open=0,
    qnb_close=0,
    fawry_open=0,
    fawry_close=0,
    customer_debts=None,
    total_customer_debts=0,
    opening_tasks_completed=None,
    opening_tasks_pending=None,
    closing_tasks_completed=None,
    closing_tasks_pending=None,
    interaction_tasks_completed=None,
    interaction_tasks_pending=None,
    social_tasks_completed=None,
    social_tasks_pending=None,
    cleaning_tasks_completed=None,
    cleaning_tasks_pending=None,
    design_tasks_completed=None,
    design_tasks_pending=None,
    moderation_tasks_completed=None,
    moderation_tasks_pending=None,
):
    db = load_db()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=30,
        bottomMargin=30,
        leftMargin=30,
        rightMargin=30,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.extend(
        _build_header(
            branch=branch,
            staff_name=staff_name,
            date_str=date_str,
            shift=shift,
            staff_role=staff_role,
            job_title=job_title,
            report_type=report_type,
            styles=styles,
            db=db,
        )
    )

    if _has_section(visible_sections, "identity"):
        elements.extend(
            _build_identity_block(
                styles=styles,
                staff_name=staff_name,
                staff_role=staff_role,
                job_title=job_title,
                branch=branch,
                shift=shift,
                date_str=date_str,
            )
        )

    if _has_section(visible_sections, "summary"):
        elements.extend(
            _build_info_table(
                styles=styles,
                sales=sales,
                expenses=expenses,
                diff=diff,
                opening_cash=opening_cash,
                closing_cash=closing_cash,
            )
        )

    if _has_section(visible_sections, "digital"):
        elements.extend(
            _build_digital_table(
                styles=styles,
                opay_open=opay_open,
                opay_close=opay_close,
                opay_diff=opay_move,
                debit_open=debit_open,
                debit_close=debit_close,
                debit_diff=debit_v22,
                nbe_open=nbe_open,
                nbe_close=nbe_close,
                nbe_diff=nbe_move,
                qnb_open=qnb_open,
                qnb_close=qnb_close,
                qnb_diff=qnb_close - qnb_open,
                fawry_open=fawry_open,
                fawry_close=fawry_close,
                fawry_diff=fawry_close - fawry_open,
            )
        )

    if _has_section(visible_sections, "customer_debts"):
        elements.extend(
            _build_customer_debts_table(
                styles=styles,
                customer_debts=customer_debts or [],
                total_customer_debts=total_customer_debts,
            )
        )

    if _has_section(visible_sections, "expenses"):
        elements.extend(
            _build_expenses_table(
                styles=styles,
                expenses_list=expenses_list or [],
                exp_note=exp_note,
            )
        )

    if _has_section(visible_sections, "cash_breakdown"):
        elements.extend(
            _build_cash_breakdown_table(
                styles=styles,
                title="Opening Cash Breakdown",
                breakdown_text=opening_cash_text,
            )
        )
        elements.extend(
            _build_cash_breakdown_table(
                styles=styles,
                title="Closing Cash Breakdown",
                breakdown_text=closing_cash_text,
            )
        )

    if _has_section(visible_sections, "tasks"):
        task_sections = [
            ("Opening Tasks", opening_tasks_completed, opening_tasks_pending),
            ("Closing Tasks", closing_tasks_completed, closing_tasks_pending),
            ("Interaction Tasks", interaction_tasks_completed, interaction_tasks_pending),
            ("Social Tasks", social_tasks_completed, social_tasks_pending),
            ("Cleaning Tasks", cleaning_tasks_completed, cleaning_tasks_pending),
            ("Design Tasks", design_tasks_completed, design_tasks_pending),
            ("Moderation Tasks", moderation_tasks_completed, moderation_tasks_pending),
        ]

        for title, completed, pending in task_sections:
            if _has_task_data(completed, pending):
                elements.extend(
                    _build_task_status_table(
                        styles,
                        title,
                        completed or [],
                        pending or [],
                    )
                )

    if _has_section(visible_sections, "interaction_notes"):
        elements.extend(
            _build_notes_section(
                styles,
                "Interaction Notes",
                interaction_notes or "No Interaction Notes",
            )
        )

    if _has_section(visible_sections, "social_notes"):
        elements.extend(
            _build_notes_section(
                styles,
                "Social Notes",
                social_notes or "No Social Notes",
            )
        )

    if _has_section(visible_sections, "special_notes"):
        elements.extend(
            _build_notes_section(
                styles,
                _get_special_notes_title(report_type),
                special_notes or "No Special Notes",
            )
        )

    if _has_section(visible_sections, "printers"):
        elements.extend(_build_printer_table(printer_diff or {}, styles))

    doc.build(elements)
    return buffer.getvalue()
