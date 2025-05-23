from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ChatMessage, Session as UserSession, Track
from app.models import Track, AnalysisResult
from fastapi import Query
import json
from sqlalchemy.orm import joinedload
import uuid

router = APIRouter(prefix="/sessions", redirect_slashes=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_or_get_session(
    session_name: str = Body(...),
    user_id: int = Body(...),
    db: Session = Depends(get_db)
):
    existing = db.query(UserSession).filter_by(session_name=session_name, user_id=user_id).first()
    if existing:
        return {"id": existing.id, "session_name": existing.session_name}

    session_id = str(uuid.uuid4())
    new_session = UserSession(id=session_id, session_name=session_name, user_id=user_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"id": new_session.id, "session_name": new_session.session_name}



# GET /sessions → list all sessions
@router.get("/")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(UserSession).all()
    return [{"id": s.id, "session_name": s.session_name} for s in sessions]


@router.get("/{id}")
def get_session(id: str, db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(UserSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# GET /sessions/{id}/tracks — list all tracks in a session
@router.get("/{id}/tracks")
def get_tracks_for_session(
    id: str,
    type: str = Query(default=None, description="Filter by track type"),
    track_name: str = Query(default=None, description="Filter by partial name match"),
    sort_by: str = Query(default="uploaded_at", enum=["uploaded_at", "track_name"]),
    sort_order: str = Query(default="desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db)
):
    print("Fetching tracks for session ID:", id)
    session = db.query(UserSession).filter(UserSession.id == id).first()
    if not session:
        print("⚠️ No session found!")
        raise HTTPException(status_code=404, detail="Session not found")

    # ✅ FIX: Use correct ID for feedback query
    feedback_lookup = {
        msg.track_id: msg.message
        for msg in db.query(ChatMessage)
        .filter(ChatMessage.session_id == id, ChatMessage.sender == "assistant", ChatMessage.track_id != None)
        .order_by(ChatMessage.timestamp.desc())
        .all()
    }

    query = db.query(Track).filter(Track.session_id == id)

    if type:
        query = query.filter(Track.type.ilike(type))
    if track_name:
        query = query.filter(Track.track_name.ilike(f"%{track_name}%"))

    if sort_by == "uploaded_at":
        query = query.order_by(Track.uploaded_at.desc() if sort_order == "desc" else Track.uploaded_at.asc())
    else:
        query = query.order_by(Track.track_name.desc() if sort_order == "desc" else Track.track_name.asc())

    tracks = query.all()

    result = []
    for track in tracks:
        analysis_data = None
        if track.analysis:
            try:
                band_energies = json.loads(track.analysis.band_energies)
            except:
                band_energies = {}

            try:
                issues = json.loads(track.analysis.issues)
            except:
                issues = []

            analysis_data = {
                "peak_db": track.analysis.peak_db,
                "rms_db": track.analysis.rms_db,
                "lufs": track.analysis.lufs,
                "dynamic_range": track.analysis.dynamic_range,
                "stereo_width_ratio": track.analysis.stereo_width_ratio,
                "stereo_width": track.analysis.stereo_width,
                "key": track.analysis.key,
                "tempo": track.analysis.tempo,
                "low_end_energy_ratio": track.analysis.low_end_energy_ratio,
                "bass_profile": track.analysis.bass_profile,
                "band_energies": band_energies,
                "issues": issues
            }

        result.append({
            "id": track.id,
            "track_name": track.track_name,
            "type": track.type,
            "file_path": track.file_path,
            "uploaded_at": track.uploaded_at,
            "analysis": analysis_data,
            "feedback": feedback_lookup.get(track.id, "")
        })

    return result


@router.put("/{id}")
def update_session_name(id: str, new_name: str, db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(UserSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.session_name = new_name
    db.commit()
    return {"message": "Session updated", "session": session}

# DELETE /sessions/{id}
@router.delete("/{id}")
def delete_session(id: str, db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(UserSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Optional: Delete all related tracks and chat messages too
    db.query(Track).filter(Track.session_id == id).delete()
    db.delete(session)
    db.commit()
    return {"message": "Session and associated tracks deleted"}