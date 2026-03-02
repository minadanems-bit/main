import io
import base64
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import streamlit as st
from database import load_db

db = load_db()


# =====================================================
# CREATE SHIFT PDF
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
        debit_v22
):
    """
    ✅ SAFE VERSION
    ✅ Prevent LayoutError
    ✅ Auto page breaks
    ✅ Safe printer loop
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=30,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    # =====================================================
    # STYLES
    # =====================================================

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        alignment=1,
        spaceAfter=15,
        textColor=colors.darkblue
    )

    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=11,
        alignment=1,
        spaceAfter=20
    )

    # =====================================================
    # HEADER
    # =====================================================

    logo_img = ""
    staff_img = ""

    if db.get("logo"):
        try:
            logo_bytes = base64.b64decode(db["logo"])
            logo_img = Image(
                io.BytesIO(logo_bytes),
                width=1.2 * inch,
                height=1.2 * inch
            )
        except:
            logo_img = ""

    staff_data = db.get("users", {}).get(st.session_state.get("user"), {})

    if staff_data.get("photo"):
        try:
            staff_bytes = base64.b64decode(staff_data["photo"])
            staff_img = Image(
                io.BytesIO(staff_bytes),
                width=1.0 * inch,
                height=1.0 * inch
            )
        except:
            staff_img = ""

    header_table = Table(
        [[logo_img, Paragraph(f"<b>NMS SHIFT REPORT</b><br/>{branch}", title_style), staff_img]],
        colWidths=[2 * inch, 6 * inch, 2 * inch]
    )

    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph(f"Date: {date_str} | Staff: {staff_name}", sub_style)
    )

    elements.append(PageBreak())  # 🔥 فصل الهيدر عن المحتوى

    # =====================================================
    # FINANCIAL TABLE
    # =====================================================

    elements.append(Paragraph("💰 Financial Summary", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    fin_table_data = [
        ["Item", "Value", "Notes"],
        ["Total Sales", f"{sales:,.2f}", "-"],
        ["Expenses", f"{expenses:,.2f}", exp_note],
        ["Opay Movement", f"{opay_move:,.2f}", "-"],
        ["Debit / V22", f"{debit_v22:,.2f}", "-"],
        ["NET Difference", f"{diff:,.2f}", "Final Result"]
    ]

    fin_table = Table(fin_table_data,
                      colWidths=[3 * inch, 3 * inch, 4 * inch])

    fin_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))

    elements.append(fin_table)

    elements.append(PageBreak())  # 🔥 فصل الجدول المالي

    # =====================================================
    # PRINTER TABLE (SAFE + DYNAMIC)
    # =====================================================

    elements.append(Paragraph("🖨 Printer Analysis", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    printer_table_data = [
        ["Printer", "Used", "Jam", "1-Side", "2-Side"]
    ]

    for printer_name, values in (printer_diff or {}).items():

        used = values.get("used", 0)
        jam = values.get("jam", 0)
        one_side = values.get("1s", 0)
        two_side = values.get("2s", 0)

        printer_table_data.append([
            printer_name,
            used,
            jam,
            one_side,
            two_side
        ])

    printer_table = Table(
        printer_table_data,
        colWidths=[
            2.5 * inch,
            1.5 * inch,
            1.5 * inch,
            1.5 * inch,
            1.5 * inch
        ]
    )

    printer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    elements.append(printer_table)

    # =====================================================
    # SAFETY: Prevent Layout Explosion
    # =====================================================

    elements.append(Spacer(1, 30))
    elements.append(PageBreak())  # 🔥 يمنع تكدس المحتوى

    # =====================================================
    # BUILD PDF
    # =====================================================

    try:
        doc.build(elements)
    except Exception as e:
        st.error(f"PDF Build Error: {e}")

    return buffer.getvalue()
