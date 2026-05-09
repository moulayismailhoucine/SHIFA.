"""PDF generation for ordonnances using ReportLab."""

import os
from datetime import date
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from app.config import get_settings

settings = get_settings()


def generate_ordonnance_pdf(
    ordonnance_id: int,
    patient_name: str,
    doctor_name: str,
    doctor_specialty: Optional[str],
    medications: List[dict],
    instructions: Optional[str],
    issued_date: date,
    valid_until: Optional[date],
) -> str:
    """Generate PDF and return relative path."""
    pdf_dir = Path(settings.upload_dir) / "ordonnances"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    filename = f"ordonnance_{ordonnance_id}_{issued_date.strftime('%Y%m%d')}.pdf"
    filepath = pdf_dir / filename
    relative = f"ordonnances/{filename}"

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0f4c81"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#555555"),
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        fontName="Helvetica-Bold",
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#111111"),
    )

    story = []

    # Header
    story.append(Paragraph("🏥 MediSys Hospital", title_style))
    story.append(Paragraph("Medical Prescription / Ordonnance", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f4c81")))
    story.append(Spacer(1, 6 * mm))

    # Patient / Doctor info
    info_data = [
        ["Patient:", patient_name, "Date:", issued_date.strftime("%d %b %Y")],
        ["Doctor:", doctor_name, "Valid Until:", valid_until.strftime("%d %b %Y") if valid_until else "—"],
        ["Specialty:", doctor_specialty or "—", "Ref #:", f"ORD-{ordonnance_id:05d}"],
    ]
    info_table = Table(info_data, colWidths=[35 * mm, 60 * mm, 35 * mm, 45 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#333333")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4 * mm))

    # Medications table
    story.append(Paragraph("Prescribed Medications", label_style))
    story.append(Spacer(1, 3 * mm))

    if medications:
        med_headers = ["#", "Medication", "Dosage", "Frequency", "Duration"]
        med_data = [med_headers]
        for i, med in enumerate(medications, 1):
            med_data.append([
                str(i),
                med.get("name", ""),
                med.get("dose", ""),
                med.get("frequency", ""),
                med.get("duration", ""),
            ])
        med_table = Table(med_data, colWidths=[10 * mm, 55 * mm, 30 * mm, 40 * mm, 35 * mm])
        med_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f4c81")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f6ff")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(med_table)
    else:
        story.append(Paragraph("No medications prescribed.", value_style))

    story.append(Spacer(1, 6 * mm))

    # Instructions
    if instructions:
        story.append(Paragraph("Instructions:", label_style))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(instructions, value_style))
        story.append(Spacer(1, 6 * mm))

    # Signature area
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 8 * mm))
    sig_data = [["Doctor's Signature:", "", "Patient Signature:", ""]]
    sig_table = Table(sig_data, colWidths=[50 * mm, 55 * mm, 50 * mm, 20 * mm])
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#555555")),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 15 * mm))

    # Footer disclaimer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#888888"),
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "This prescription is generated by MediSys Hospital Management System. "
        "It is valid only with an authorized doctor's signature and stamp. "
        "Unauthorized reproduction or alteration is prohibited.",
        footer_style,
    ))

    doc.build(story)
    return relative
