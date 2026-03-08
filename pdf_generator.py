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


def _build_header(branch: str, staff_name: str, date_str: str, styles, db: dict):
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
        [[logo_img, Paragraph(f"<b>NMS SHIFT REPORT</b><br/>{branch}", title_style), staff_img]],
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

    meta = Paragraph(f"Date: {date_str} | Staff: {staff_name}", sub_style)
    return [header_table, Spacer(1, 10), meta, Spacer(1, 18)]


def _build_financial_table(
    sales,
    expenses,
    exp_note,
    diff,
    opay_move,
    debit_v22,
    styles,
):
    normal_style = styles["Normal"]

    safe_exp_note = Paragraph(str(exp_note or "-").replace("\n", "<br/>"), normal_style)

    table_data = [
        ["Item", "Value", "Notes"],
        ["Total Sales", f"{_safe_number(sales):,.2f}", "-"],
        ["Expenses", f"{_safe_number(expenses):,.2f}", safe_exp_note],
        ["Opay Movement", f"{_safe_number(opay_move):,.2f}", "-"],
        ["Debit Movement", f"{_safe_number(debit_v22):,.2f}", "-"],
        ["Net Difference", f"{_safe_number(diff):,.2f}", "Final Result"],
    ]

    table = Table(
        table_data,
        colWidths=[3 * inch, 2.5 * inch, 4.5 * inch],
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
        Paragraph("💰 Financial Summary", styles["Heading2"]),
        Spacer(1, 10),
        table,
        Spacer(1, 20),
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
        Paragraph("🖨 Printer Analysis", styles["Heading2"]),
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
):
    """
    Generate a shift PDF report and return bytes.
    """

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

    elements.extend(_build_header(branch, staff_name, date_str, styles, db))
    elements.extend(
        _build_financial_table(
            sales=sales,
            expenses=expenses,
            exp_note=exp_note,
            diff=diff,
            opay_move=opay_move,
            debit_v22=debit_v22,
            styles=styles,
        )
    )
    elements.extend(_build_printer_table(printer_diff or {}, styles))

    doc.build(elements)
    return buffer.getvalue()
