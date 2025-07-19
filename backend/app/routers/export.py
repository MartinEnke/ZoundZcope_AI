from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ChatMessage
from app.gpt_utils import generate_feedback_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from fastapi.responses import StreamingResponse

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
You are an experienced audio engineer helping a user improve their mix/master.

Here is the AI feedback you previously generated for their track:

\"\"\"
{feedback_text}
\"\"\"

Based solely on this feedback, please provide recommended parameter adjustments for the following Ableton devices:

1. EQ8 — specify gain adjustments, frequency bands, filter types (e.g., low shelf, bell) clearly.
2. Glue Compressor — specify threshold, ratio, attack, release, and makeup gain.

Format your response exactly like this:

EQ8:
- Band 1: Gain -3dB at 100Hz, Low Shelf
- Band 2: Gain +2dB at 2kHz, Bell
- Band 3: Bypass

Glue Compressor:
- Threshold: -18 dB
- Ratio: 4:1
- Attack: 10 ms
- Release: 150 ms
- Makeup Gain: 2 dB

Only list the parameters and values, no extra explanation.
"""
    return generate_feedback_response(prompt)


def create_pdf(feedback_text: str, preset_text: str) -> BytesIO:
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin

    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin, y, "AI Mixing & Mastering Feedback and Presets Export")
    y -= 30

    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "AI Feedback:")
    y -= 20

    p.setFont("Helvetica", 10)
    for line in feedback_text.split("\n"):
        if y < 50:
            p.showPage()
            y = height - margin
            p.setFont("Helvetica", 10)
        p.drawString(margin, y, line)
        y -= 14

    y -= 20
    p.setFont("Helvetica-Bold", 12)
    if y < 80:
        p.showPage()
        y = height - margin
    p.drawString(margin, y, "Recommended Ableton Preset Parameters:")
    y -= 20

    p.setFont("Helvetica", 10)
    for line in preset_text.split("\n"):
        if y < 50:
            p.showPage()
            y = height - margin
            p.setFont("Helvetica", 10)
        p.drawString(margin, y, line)
        y -= 14

    p.save()
    buffer.seek(0)
    return buffer

@router.get("/export-feedback-presets")
def export_feedback_presets(
    session_id: str = Query(...),
    track_id: str = Query(...),
    db: Session = Depends(get_db)
):
    feedback_text = get_feedback_text(session_id, track_id, db)
    if not feedback_text:
        raise HTTPException(status_code=404, detail="No feedback found for this session and track")

    preset_text = generate_preset_text_from_feedback(feedback_text)
    pdf_buffer = create_pdf(feedback_text, preset_text)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=feedback_presets_{session_id}_{track_id}.pdf"
        }
    )
