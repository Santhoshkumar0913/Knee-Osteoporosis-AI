"""On-demand PDF reports for saved analyses and current Clinical Support."""
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


NAVY = colors.HexColor("#102a43")
LIGHT_BLUE = colors.HexColor("#eef4fb")
MID_GREY = colors.HexColor("#52606d")
LINE = colors.HexColor("#d9e2ec")


def _display(value: Any, fallback: str = "Not specified") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _paragraph_text(value: Any) -> str:
    plain_text = _display(value)
    for dash in ("‐", "‑", "‒", "–", "—", "−"):
        plain_text = plain_text.replace(dash, "-")
    plain_text = (
        plain_text.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("•", "-")
        .replace("\u00a0", " ")
    )
    return escape(plain_text).replace("\n", "<br/>")


def _section_heading(text: str, styles: dict) -> Paragraph:
    return Paragraph(escape(text), styles["section"])


def _key_value_table(rows: list[tuple[str, Any]], styles: dict) -> Table:
    data = [
        [Paragraph(escape(label), styles["label"]), Paragraph(_paragraph_text(value), styles["value"])]
        for label, value in rows
    ]
    table = Table(data, colWidths=[1.8 * inch, 4.75 * inch], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (0, -1), MID_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
    ]))
    return table


def _text_block(title: str, text: str, styles: dict) -> list:
    return [
        Paragraph(escape(title), styles["subsection"]),
        Paragraph(_paragraph_text(text), styles["body"]),
        Spacer(1, 5),
    ]


def _list_block(title: str, items: list[str], styles: dict) -> list:
    content = [Paragraph(escape(title), styles["subsection"])]
    if items:
        content.extend(Paragraph(f"- {_paragraph_text(item)}", styles["body"]) for item in items)
    else:
        content.append(Paragraph("No items provided for this section.", styles["muted"]))
    content.append(Spacer(1, 5))
    return content


def _draw_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(document.leftMargin, 0.48 * inch, A4[0] - document.rightMargin, 0.48 * inch)
    canvas.setFillColor(MID_GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(document.leftMargin, 0.3 * inch, "Knee Osteoporosis AI - Clinical Support Report")
    canvas.drawRightString(A4[0] - document.rightMargin, 0.3 * inch, f"Page {document.page}")
    canvas.restoreState()


def generate_clinical_support_report(
    analysis: Any,
    patient: Any,
    clinical_support: Any,
    image_path: Path,
) -> bytes:
    """Build a report in memory from saved analysis data and the current response."""
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError("Saved analysis image was not found")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=21, leading=25, textColor=NAVY, alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, leading=14, textColor=MID_GREY, alignment=TA_CENTER,
        spaceAfter=13,
    ))
    styles.add(ParagraphStyle(
        name="ReportSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=NAVY, spaceBefore=11, spaceAfter=6,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubsection", parent=styles["Heading3"], fontName="Helvetica-Bold",
        fontSize=9.5, leading=12, textColor=NAVY, spaceBefore=4, spaceAfter=3,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="ReportLabel", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8.5, leading=11, textColor=MID_GREY,
    ))
    styles.add(ParagraphStyle(
        name="ReportValue", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=12, textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="ReportBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.2, leading=13, textColor=colors.HexColor("#243b53"),
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="ReportMuted", parent=styles["BodyText"], fontName="Helvetica-Oblique",
        fontSize=8.5, leading=11, textColor=MID_GREY,
    ))
    # Keep styles under stable keys for the table and content helpers.
    styles_by_key = {
        "section": styles["ReportSection"],
        "subsection": styles["ReportSubsection"],
        "label": styles["ReportLabel"],
        "value": styles["ReportValue"],
        "body": styles["ReportBody"],
        "muted": styles["ReportMuted"],
    }

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.68 * inch,
        title="Knee Osteoporosis AI - Clinical Support Report",
        author="Knee Osteoporosis AI",
    )

    analysis_date = analysis.created_at.strftime("%d %b %Y")
    patient_rows = [
        ("Patient ID", patient.id),
        ("Patient Code", patient.patient_code),
        ("Name", patient.name),
        ("Age", f"{analysis.age} years"),
        ("Gender", analysis.gender),
        ("Analysis Date", analysis_date),
    ]
    clinical_context_rows = [
        ("Height", f"{analysis.height:.2f} m"),
        ("Weight", f"{analysis.weight:g} kg"),
        ("BMI", f"{analysis.bmi:.1f}"),
        ("Joint Pain", analysis.joint_pain),
        ("Number of Pregnancies", analysis.pregnancies),
        ("Menopausal Status", "Not applicable" if str(analysis.gender).lower() == "male" else analysis.menopausal_status),
        ("Smoking", analysis.smoking),
        ("Alcohol", analysis.alcohol),
        ("Previous Fracture", analysis.previous_fracture),
        ("Long-term Steroid Use", analysis.long_term_steroid_use),
    ]
    prediction_rows = [
        ("Predicted Class", analysis.predicted_diagnosis),
        ("Confidence", f"{analysis.confidence * 100:.1f}%"),
        ("Normal Probability", f"{analysis.normal_probability * 100:.1f}%"),
        ("Osteopenia Probability", f"{analysis.osteopenia_probability * 100:.1f}%"),
        ("Osteoporosis Probability", f"{analysis.osteoporosis_probability * 100:.1f}%"),
    ]
    bone_score_rows = [
        ("Model-estimated T-score", f"{analysis.t_score:.2f}"),
        ("T-score Range", f"{analysis.t_score_lower:.2f} to {analysis.t_score_upper:.2f}"),
        ("Model-estimated Z-score", f"{analysis.z_score:.2f}"),
        ("Z-score Range", f"{analysis.z_score_lower:.2f} to {analysis.z_score_upper:.2f}"),
    ]

    story = [
        Paragraph("Knee Osteoporosis AI", styles["ReportTitle"]),
        Paragraph("Clinical Support Report", styles["ReportSubtitle"]),
        _section_heading("1. Patient Information", styles_by_key),
        _key_value_table(patient_rows, styles_by_key),
        _section_heading("2. Clinical Context", styles_by_key),
        _key_value_table(clinical_context_rows, styles_by_key),
        _section_heading("3. X-ray Analysis - Original X-ray", styles_by_key),
    ]

    # Normalize supported input formats for ReportLab while preserving the original image.
    with PILImage.open(image_path) as saved_image:
        image_buffer = BytesIO()
        saved_image.convert("RGB").save(image_buffer, format="PNG")
    image_buffer.seek(0)
    xray = Image(image_buffer)
    xray._restrictSize(4.5 * inch, 4.1 * inch)
    xray.hAlign = "CENTER"
    story.extend([xray, Spacer(1, 5)])

    story.extend([
        _section_heading("4. Model Prediction", styles_by_key),
        _key_value_table(prediction_rows, styles_by_key),
        _section_heading("5. Bone Score Estimates", styles_by_key),
        _key_value_table(bone_score_rows, styles_by_key),
        _section_heading("6. Clinical Support", styles_by_key),
    ])
    story.extend(_text_block("Explanation", clinical_support.explanation, styles_by_key))
    story.extend(_list_block("What You Can Do Now", clinical_support.what_you_can_do_now, styles_by_key))
    story.extend(_list_block("Talk to Your Doctor About", clinical_support.talk_to_your_doctor_about, styles_by_key))
    story.extend(_list_block("Testing and Follow-up", clinical_support.testing_and_follow_up, styles_by_key))
    story.extend(_list_block("Treatment Information", clinical_support.treatment_information, styles_by_key))

    story.append(_section_heading("7. Evidence Sources", styles_by_key))
    if clinical_support.sources:
        for source in clinical_support.sources:
            organization = source.get("organization") if isinstance(source, dict) else source.organization
            year = source.get("year") if isinstance(source, dict) else source.year
            story.append(Paragraph(
                f"- {_paragraph_text(organization)} ({_paragraph_text(year)})",
                styles_by_key["body"],
            ))
    else:
        story.append(Paragraph("No sources were retrieved for this response.", styles_by_key["muted"]))

    story.extend([
        _section_heading("8. Grounding Note", styles_by_key),
        Paragraph(_paragraph_text(clinical_support.grounding_note), styles_by_key["body"]),
        _section_heading("9. Disclaimer", styles_by_key),
        Paragraph(_paragraph_text(clinical_support.disclaimer), styles_by_key["body"]),
    ])

    document.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    return buffer.getvalue()
