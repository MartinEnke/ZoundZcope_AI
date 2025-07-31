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
from xml.sax.saxutils import escape
import re


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





def render_line_with_bold(line: str, style: ParagraphStyle) -> Paragraph:
    # Convert **text** into bold using <b> tags
    line = escape(line)
    line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
    return Paragraph(line, style)


def create_comparison_pdf(feedback_text: str, preset_text: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()

    # Base styles
    company_title_style = ParagraphStyle('CompanyTitle', fontName='Helvetica-Bold', fontSize=24, alignment=TA_CENTER, spaceAfter=28)
    subheadline_style = ParagraphStyle('Subheadline', fontName='Helvetica-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=32)
    section_h2_style = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=14, spaceAfter=14)
    section_h3_style = ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=12, spaceAfter=10)
    normal_style = ParagraphStyle('Normal', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=6)
    plugin_name_style = ParagraphStyle('PluginName', fontName='Helvetica-Bold', fontSize=10, spaceAfter=2)
    plugin_data_style = ParagraphStyle('PluginData', fontName='Helvetica', fontSize=10, leftIndent=12, spaceAfter=2)

    elements = []

    # Header
    elements.append(Paragraph("ZoundZcope AI", company_title_style))
    elements.append(Paragraph("Multi-Track Comparison + Presets Report", subheadline_style))

    # Section: Feedback
    elements.append(Paragraph("AI Comparison Feedback:", section_h2_style))

    # --- Feedback Formatting ---
    numbered_group = []
    bullet_group = []

    def flush_numbered_group():
        nonlocal numbered_group
        if numbered_group:
            list_items = [ListItem(render_line_with_bold(item, normal_style)) for item in numbered_group]
            elements.append(ListFlowable(list_items, bulletType='1', start='1'))
            numbered_group = []

    def flush_bullet_group():
        nonlocal bullet_group
        if bullet_group:
            list_items = [ListItem(render_line_with_bold(item, normal_style)) for item in bullet_group]
            elements.append(ListFlowable(list_items, bulletType='bullet'))
            bullet_group = []

    lines = feedback_text.strip().split("\n")

    # ✅ Remove the first line if it's the unwanted heading
    if lines and lines[0].strip() == "### Comparison of Tracks":
        lines = lines[1:]

    # ✅ Now loop over the cleaned lines
    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush_bullet_group()
            flush_numbered_group()
            elements.append(Spacer(1, 6))
            continue

        if stripped.startswith("### "):
            flush_bullet_group()
            flush_numbered_group()
            elements.append(Paragraph(stripped[4:], section_h2_style))
        elif stripped.startswith("#### "):
            flush_bullet_group()
            flush_numbered_group()
            elements.append(Paragraph(stripped[5:], section_h3_style))
        elif re.match(r"^\d+\.\s", stripped):  # Numbered list
            numbered_group.append(stripped)
        elif stripped.startswith("- "):
            bullet_group.append(stripped[2:])
        else:
            flush_bullet_group()
            flush_numbered_group()
            elements.append(render_line_with_bold(stripped, normal_style))

    flush_bullet_group()
    flush_numbered_group()

    elements.append(Spacer(1, 12))

    # Section: Presets
    elements.append(Paragraph("Recommended Ableton Preset Parameters:", section_h2_style))

    # --- Preset Formatting ---
    bullet_group = []

    def flush_preset_group():
        nonlocal bullet_group
        if bullet_group:
            list_items = [ListItem(render_line_with_bold(item, plugin_data_style)) for item in bullet_group]
            elements.append(ListFlowable(list_items, bulletType='bullet'))
            bullet_group = []

    for line in preset_text.strip().split("\n"):
        stripped = line.strip()

        if not stripped:
            flush_preset_group()
            elements.append(Spacer(1, 6))
            continue

        if any(stripped.startswith(p) for p in ["EQ8:", "Compressor:", "Glue Compressor:", "Limiter:", "Multiband Dynamics:", "Utils:"]):
            flush_preset_group()
            elements.append(Paragraph(stripped, plugin_name_style))
        elif stripped.startswith("- "):
            bullet_group.append(stripped[2:])
        else:
            flush_preset_group()
            elements.append(render_line_with_bold(stripped, normal_style))

    flush_preset_group()

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


def generate_presets_from_comparison_feedback(feedback_text: str) -> str:
    prompt = f"""
You are an expert audio engineer assisting with a comparison of multiple tracks.

Below is the multi-track comparison feedback that was previously generated:

\"\"\"
{feedback_text}
\"\"\"

Now generate **only** the recommended plugin and preset parameters that could help resolve the issues or enhance cohesion, based on the feedback above.

Output the results under the following section:

---

Recommended Ableton Preset Parameters:

EQ8:
- Band 1: [freq, gain, Q, bell/shelf, notes]
- Band 2: ...

Compressor:
- Threshold: ...
- Ratio: ...
- Attack: ...
- Release: ...

Multiband Dynamics:
- ...

Limiter:
- ...

Utils:
- ...

(Only include relevant plugins. Provide short notes in parentheses if needed.)

---

Rules:
- DO NOT repeat the feedback text.
- DO NOT add commentary, explanation, or headings outside of the preset section.
- ONLY output plain text in the format above, starting directly with 'Recommended Ableton Preset Parameters:'.
"""
    return generate_feedback_response(prompt)



@router.get("/export-comparison")
def export_comparison_feedback(group_id: str = Query(...), db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.comparison_group_id == group_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No comparison feedback found")

    first_msg = next((m for m in messages if m.message and m.message.strip()), messages[0])
    feedback_text = first_msg.message

    preset_text = generate_presets_from_comparison_feedback(feedback_text)
    pdf_buffer = create_comparison_pdf(feedback_text, preset_text)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=comparison_feedback_{group_id}.pdf"
        }
    )
