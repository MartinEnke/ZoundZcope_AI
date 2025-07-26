from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, ChatMessage
from app.gpt_utils import generate_feedback_response
from reportlab.lib.pagesizes import letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from reportlab.lib.utils import simpleSplit
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.enums import TA_CENTER


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_feedback_text(session_id: str, track_id: str, db: Session) -> str:
    messages = (
        db.query(ChatMessage)
        .filter_by(session_id=session_id, track_id=track_id, sender='assistant')
        .order_by(ChatMessage.timestamp)
        .all()
    )
    return "\n\n".join(msg.message for msg in messages)


def generate_preset_text_from_feedback(feedback_text: str) -> str:
    prompt = f"""

Here is the AI feedback you generated previously:

\"\"\"
{feedback_text}
\"\"\"

You are generating a report for ZoundZcope AI.

Please output the content exactly as follows, with these section headings and formatting:

---

ZoundZcope AI

Mixing & Mastering Feedback and Presets Report

AI Feedback:

- ISSUE:
  [Describe the issue clearly in a few sentences.]

- IMPROVEMENT:
  [Describe the suggested improvement clearly.]

(Repeat multiple ISSUE and IMPROVEMENT pairs as needed.)

Recommended Ableton Preset Parameters:

EQ8:
- Band 1: [parameters like frequency, gain, Q, shelf/bell + a brief note in brackets]
- Band 2: [parameters like frequency, gain, Q, shelf/bell + a brief note in brackets]
(Repeat for more bands if needed)

Compressor:
- Threshold: [value]
- Ratio: [value]
- Attack: [value]
- Release: [value]
- Makeup Gain: [value]

Transient Shaper:
- [Parameters]: [value]
(Repeat for more parameters if needed)

Multiband Dynamics:
- [Parameters]: [value]
(Repeat for more parameters if needed)

Limiter:
- [Parameters]: [value]
(Repeat for more parameters if needed)

Utils:
- [Parameters]: [value]
(Repeat for more parameters if needed)


(Include plugins relevant to the feedback. Provide brief notes in parentheses explaining the purpose of adjustments.)

---

Notes:

- Use exactly the headings and labels shown above.
- Keep "ZoundZcope AI" as the main title.
- Use "Mixing & Mastering Feedback and Presets Report" as the subtitle.
- Use "AI Feedback:" and "Recommended Ableton Preset Parameters:" as section headers.
- Use uppercase "ISSUE:" and "IMPROVEMENT:" labels.
- List plugin names like "EQ8:" and "Compressor:" exactly as shown.
- Use simple bullet points with dashes (-) for parameters.
- Do NOT include any markdown formatting, HTML tags, or extra decorations.
- Only output plain text with line breaks as shown.

Generate the content now:
"""
    return generate_feedback_response(prompt)




def draw_wrapped_text(p, text, x, y, max_width, line_height=14):
    lines = simpleSplit(text, "Helvetica", 10, max_width)
    for line in lines:
        if y < 50:
            p.showPage()
            y = letter[1] - 40
            p.setFont("Helvetica", 10)
        p.drawString(x, y, line)
        y -= line_height
    return y


def create_pdf(full_report_text: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    # Define styles
    styles = getSampleStyleSheet()

    company_title_style = ParagraphStyle(
        'CompanyTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    subheadline_style = ParagraphStyle(
        'Subheadline',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=18
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        spaceAfter=10
    )

    uppercase_bold_style = ParagraphStyle(
        'UppercaseBold',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        'Normal',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    plugin_name_style = ParagraphStyle(
        'PluginName',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        spaceAfter=2
    )

    plugin_data_style = ParagraphStyle(
        'PluginData',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        leftIndent=12,
        spaceAfter=2
    )

    elements = []

    # Split lines
    lines = [line.strip() for line in full_report_text.strip().split("\n")]

    # For grouping bullet points (plugin parameters)
    bullet_group = []

    def flush_bullet_group():
        nonlocal bullet_group
        if bullet_group:
            bullet_items = [ListItem(Paragraph(item, plugin_data_style)) for item in bullet_group]
            elements.append(ListFlowable(bullet_items, bulletType='bullet'))
            bullet_group = []

    for line in lines:
        if not line:
            flush_bullet_group()
            elements.append(Spacer(1, 8))
            continue

        # Company title
        if line.lower().startswith("zoundzcope ai"):
            flush_bullet_group()
            elements.append(Paragraph(line, company_title_style))
            continue

        # Subheadline
        if "feedback and presets report" in line.lower():
            flush_bullet_group()
            elements.append(Paragraph(line, subheadline_style))
            continue

        # Section headers
        if line in ["AI Feedback:", "Recommended Ableton Preset Parameters:"]:
            flush_bullet_group()
            elements.append(Paragraph(line, section_header_style))
            continue

        # Uppercase ISSUE / IMPROVEMENT labels
        if line.startswith("- ISSUE:") or line.startswith("- IMPROVEMENT:"):
            flush_bullet_group()
            label, _, rest = line.partition(":")
            label = label.replace("- ", "").upper() + ":"
            elements.append(Paragraph(label, uppercase_bold_style))
            if rest.strip():
                elements.append(Paragraph(rest.strip(), normal_style))
            continue

        # Plugin names (bold)
        if any(line.startswith(plugin) for plugin in ["EQ8:", "Compressor:", "Glue Compressor:", "Limiter:", "Multiband Dynamics:", "Utils:"]):
            flush_bullet_group()
            elements.append(Paragraph(line, plugin_name_style))
            continue

        # Plugin data bullet points (collect in group)
        if line.startswith("- "):
            bullet_group.append(line[2:].strip())
            continue

        # Default normal text
        flush_bullet_group()
        elements.append(Paragraph(line, normal_style))

    # Flush leftover bullets at the end
    flush_bullet_group()

    doc.build(elements)
    buffer.seek(0)
    return buffer




@router.get("/export-feedback-presets")
def export_feedback_presets(
    session_id: str = Query(...),
    track_id: str = Query(...),
    db: Session = Depends(get_db)
):
    print(f"Export request for session {session_id}, track {track_id}")

    # Fetch the track object
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # Detect if this is a reference track by name or however you identify it
    if "(Reference)" in (track.track_name or ""):
        # Find main track(s) for this session excluding reference tracks
        main_track = (
            db.query(Track)
            .filter(
                Track.session_id == session_id,
                ~Track.track_name.contains("(Reference)"),
            )
            .order_by(Track.uploaded_at.desc())
            .first()
        )

        if not main_track:
            raise HTTPException(
                status_code=404,
                detail="No main track found for this session to export feedback",
            )
        print(f"Reference track detected, switching export to main track {main_track.id}")
        track_id = main_track.id

    # Now fetch feedback messages for the track_id (could be original or switched)
    messages = (
        db.query(ChatMessage)
        .filter_by(session_id=session_id, track_id=track_id, sender='assistant')
        .order_by(ChatMessage.timestamp)
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No feedback found for this session and track")

    feedback_text = "\n\n".join(msg.message for msg in messages)

    full_report = generate_preset_text_from_feedback(feedback_text)
    pdf_buffer = create_pdf(full_report)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=feedback_presets_{session_id}_{track_id}.pdf"
        }
    )
