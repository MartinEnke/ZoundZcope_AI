from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ChatMessage
from app.gpt_utils import generate_feedback_response
from reportlab.lib.pagesizes import letter
from io import BytesIO
from fastapi.responses import StreamingResponse
from reportlab.lib.utils import simpleSplit
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


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

Please use this feedback and generate a report. Include this Feedbakc as it is and suggest adjustments via 
Ableton EQ8 and Ableton Glue Compressor. No further other text or duplications.

---
Format the text like this using appropriate bold style and headline sizes:
Example output (comments in () are instructions for you) :

Zoundzcope AI 

Mixing & Mastering Feedback and Presets Report 

AI Feedback: 

- ISSUE: 
  [describe issue clearly]
- IMPROVEMENT: 
  [describe improvement clearly]

- ISSUE:
  [next issue]
- IMPROVEMENT:
  [next improvement]


Recommended Ableton Preset Parameters: 

(Based on this feedback, provide detailed and precise parameter recommendations for common Ableton devices like EQ8, 
Compressor or Glue Compressor, Limiter, Multiband Dynamics, Utility.
Format your response exactly like this example:)

EQ8:
- Band 1: Parameters, FQ etc
- Band 2: ...

Compressor:
- Threshold: -20 dB 
- Ratio: 3:1
- Attack: 15 ms
- Release: 100 ms
- Makeup Gain: 4 dB

(Only output these parameter settings related to the feedback; no generic defaults or extra explanations.)
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

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontName = 'Helvetica'
    normal_style.fontSize = 10
    normal_style.leading = 14

    bold_style = styles['Heading3']
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.leading = 16

    elements = []

    # Split the full report into lines for processing
    lines = full_report_text.strip().split("\n")

    for line in lines:
        line = line.strip()

        # Handle headlines/subheadings by keywords
        if line.startswith("Zoundzcope"):
            elements.append(Paragraph(line, styles['Heading1']))
            elements.append(Spacer(1, 12))
        elif "Feedback and Presets Report" in line:
            elements.append(Paragraph(line, styles['Heading2']))
            elements.append(Spacer(1, 12))
        elif line.endswith(":") and len(line) < 30:
            # Treat short lines ending with ':' as section headers
            elements.append(Paragraph(line, bold_style))
            elements.append(Spacer(1, 8))
        elif line.startswith("- "):
            # Bullet points
            # We'll gather consecutive bullet points in a ListFlowable
            # But for simplicity, add as paragraphs with bullet char
            bullet_line = line[2:].strip()
            elements.append(Paragraph(f"• {bullet_line}", normal_style))
        elif line == "":
            # Blank line -> spacer
            elements.append(Spacer(1, 8))
        else:
            # Normal paragraph line
            elements.append(Paragraph(line, normal_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


@router.get("/export-feedback-presets")
def export_feedback_presets(
    session_id: str = Query(...),
    track_id: str = Query(...),
    db: Session = Depends(get_db)
):
    print(f"Export request received for session {session_id}, track {track_id}")
    feedback_text = get_feedback_text(session_id, track_id, db)
    if not feedback_text:
        raise HTTPException(status_code=404, detail="No feedback found for this session and track")

    # Generate the full formatted report (feedback + presets) from GPT
    full_report = generate_preset_text_from_feedback(feedback_text)

    # Create PDF with only the full GPT report text
    pdf_buffer = create_pdf(full_report)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=feedback_presets_{session_id}_{track_id}.pdf"
        }
    )