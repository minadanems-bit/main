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


def _build_header(branch: str, staff_name: str, date_str: str, shift: str, staff_role: str, styles, db: dict):
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

    header_table = Table(
        [[logo_img, Paragraph(f"<b>NMS SHIFT REPORT</b><br/>{_safe_text(branch)}", title_style), staff_img]],
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
        f"Role: {_safe_text(staff_role)} | Shift: {_safe_text(shift)}",
        sub_style,
    )

    return [header_table, Spacer(1, 10), meta, Spacer(1, 18)]


def _build_info_table(styles, sales, expenses, diff, opening_cash, closing_cash):
    table_data = [
        ["Item", "Value"],
        ["Total Sales", f"{_safe_number(sales):,.2f} LE"],
        ["Total Expenses", f"{_safe_number(expenses):,.2f} LE"],
        ["Opening Cash", f"{_safe_number(opening_cash):,.2f} LE"],
        ["Closing Cash", f"{_safe_number(closing_cash):,.2f} LE"],
        ["Cash Difference", f"{_safe_number(diff):,.2f} LE"],
    ]

    table = Table(
        table_data,
        colWidths=[4.5 * inch, 4.5 * inch],
        repeatRows=1,
    )
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

    return [
        Paragraph("Shift Summary", styles["Heading2"]),
        Spacer(1, 10),
        table,
        Spacer(1, 18),
    ]


def _build_digital_table(styles, opay_move, debit_v22, nbe_move):
    table_data = [
        ["Channel", "Movement"],
        ["Opay", f"{_safe_number(opay_move):,.2f} LE"],
        ["Debit", f"{_safe_number(debit_v22):,.2f} LE"],
        ["NBE Wallet", f"{_safe_number(nbe_move):,.2f} LE"],
    ]

    table = Table(
        table_data,
        colWidths=[4.5 * inch, 4.5 * inch],
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

    return [
        Paragraph("Digital Payments Movement", styles["Heading2"]),
        Spacer(1, 10),
        table,
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

    table = Table(
        table_data,
        colWidths=[6 * inch, 3 * inch],
        repeatRows=1,
    )
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

    table = Table(
        table_data,
        colWidths=[9 * inch],
    )
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

    return [
        Paragraph(title, styles["Heading2"]),
        Spacer(1, 10),
        table,
        Spacer(1, 18),
    ]


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

    return [
        Paragraph("Printer Analysis", styles["Heading2"]),
        Spacer(1, 10),
        table,
        Spacer(1, 20),
    ]


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

    elements.extend(_build_header(branch, staff_name, date_str, shift, staff_role, styles, db))
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
    elements.extend(
        _build_digital_table(
            styles=styles,
            opay_move=opay_move,
            debit_v22=debit_v22,
            nbe_move=nbe_move,
        )
    )
    elements.extend(
        _build_expenses_table(
            styles=styles,
            expenses_list=expenses_list or [],
            exp_note=exp_note,
        )
    )
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
    elements.extend(_build_notes_section(styles, "Interaction Notes", interaction_notes or "No Interaction Notes"))
    elements.extend(_build_notes_section(styles, "Social Notes", social_notes or "No Social Notes"))
    elements.extend(_build_notes_section(styles, "Special Notes", special_notes or "No Special Notes"))
    elements.extend(_build_printer_table(printer_diff or {}, styles))

    doc.build(elements)
    return buffer.getvalue()
