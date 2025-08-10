"""
FastAPI router for session management in ZoundZcope.

This module provides API endpoints for creating, retrieving, updating, and
deleting user sessions. It also includes endpoints for listing all sessions,
retrieving associated tracks (with optional filters and sorting), and removing
all related data when a session is deleted.

Endpoints:
    POST   /sessions/          - Create a session or return an existing one.
    GET    /sessions/          - List all sessions.
    GET    /sessions/{id}      - Retrieve a specific session by ID.
    GET    /sessions/{id}/tracks - List all tracks in a session with optional
                                   filtering and sorting.
    PUT    /sessions/{id}      - Update the name of a session.
    DELETE /sessions/{id}      - Delete a session and all related data.
    POST   /sessions/create    - Create a new session via form submission.

Dependencies:
    - SQLAlchemy SessionLocal for database access.
    - Models: UserSession, Track, ChatMessage, AnalysisResult.
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Form
from sqlalchemy.orm import Session, joinedload
from app.database import SessionLocal
from app.models import ChatMessage, Session as UserSession, Track
from app.models import Track, AnalysisResult
from fastapi import Query
import json
import uuid

router = APIRouter(prefix="/sessions", redirect_slashes=False)


def get_db():
    """
        Provide a SQLAlchemy database session for dependency injection.

        Yields:
            Session: Active SQLAlchemy session for database operations.
        """
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
    """
        Create a new session or return an existing one for a given user.

        Args:
            session_name (str): Name of the session.
            user_id (int): ID of the user creating or retrieving the session.
            db (Session): Database session dependency.

        Returns:
            dict: Session ID and name of the created or existing session.
        """
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
    """
        List all available sessions.

        Args:
            db (Session): Database session dependency.

        Returns:
            list[dict]: List of sessions with their IDs and names.
        """
    sessions = db.query(UserSession).all()
    return [{"id": s.id, "session_name": s.session_name} for s in sessions]


@router.get("/{id}")
def get_session(id: str, db: Session = Depends(get_db)):
    """
        Retrieve a specific session by ID.

        Args:
            id (str): The UUID of the session.
            db (Session): Database session dependency.

        Raises:
            HTTPException: If the session does not exist.

        Returns:
            UserSession: The matching session object.
        """
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
    """
        Retrieve all tracks for a specific session, with optional filtering and sorting.

        Args:
            id (str): Session UUID.
            type (str, optional): Filter tracks by type (e.g., 'mixdown').
            track_name (str, optional): Filter tracks by partial name match.
            sort_by (str): Sorting field ('uploaded_at' or 'track_name').
            sort_order (str): Sort order ('asc' or 'desc').
            db (Session): Database session dependency.

        Raises:
            HTTPException: If the session does not exist.
            HTTPException: For any internal error.

        Returns:
            list[dict]: List of track details, including latest feedback and analysis results.
        """
    try:
        print(f"🟡 Looking up session ID: {id}")
        session = db.query(UserSession).filter(UserSession.id == id).first()
        if not session:
            print("⚠️ No session found for that ID.")
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

        # Exclude reference tracks by name
        query = query.filter(~Track.track_name.ilike('%(Reference)%'))

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
            band_energies = {}
            issues = []
            analysis_data = None

            if track.analysis:
                try:
                    band_energies = json.loads(track.analysis.band_energies or "{}")
                except Exception as e:
                    print(f"⚠️ Failed to parse band_energies for track {track.id}: {e}")

                try:
                    issues = json.loads(track.analysis.issues or "[]")
                except Exception as e:
                    print(f"⚠️ Failed to parse issues for track {track.id}: {e}")

                analysis_data = {
                    "peak_db": track.analysis.peak_db,
                    "rms_db": track.analysis.rms_db_peak,
                    "lufs": track.analysis.lufs,
                    "dynamic_range": track.analysis.dynamic_range,
                    "stereo_width_ratio": track.analysis.stereo_width_ratio,
                    "stereo_width": track.analysis.stereo_width,
                    "key": track.analysis.key,
                    "tempo": track.analysis.tempo,
                    "low_end_energy_ratio": track.analysis.low_end_energy_ratio,
                    "band_energies": band_energies,
                    "issues": issues,
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

    except Exception as e:
        print("❌ INTERNAL ERROR in /sessions/{id}/tracks:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id}")
def update_session_name(
    id: str,
    new_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """
        Update the name of a specific session.

        Args:
            id (str): UUID of the session to update.
            new_name (str): New session name.
            db (Session): Database session dependency.

        Raises:
            HTTPException: If the session does not exist.

        Returns:
            dict: Confirmation message and updated session object.
        """
    session = db.query(UserSession).filter(UserSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.session_name = new_name
    db.commit()
    return {"message": "Session updated", "session": session}


@router.delete("/{id}")
def delete_session(id: str, db: Session = Depends(get_db)):
    """
        Delete a session and all related data.

        This removes:
            - Chat messages linked to the session's tracks.
            - Analysis results linked to the session's tracks.
            - All tracks in the session.
            - The session itself.

        Args:
            id (str): UUID of the session to delete.
            db (Session): Database session dependency.

        Raises:
            HTTPException: If the session does not exist.

        Returns:
            dict: Confirmation message summarizing deletions.
        """
    session = db.query(UserSession).filter(UserSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all track IDs related to this session
    track_ids = [t.id for t in db.query(Track.id).filter(Track.session_id == id).all()]

    if track_ids:
        # Delete chat messages related to these tracks
        deleted_chats = db.query(ChatMessage).filter(ChatMessage.track_id.in_(track_ids)).delete(synchronize_session=False)
        print(f"Deleted {deleted_chats} chat messages linked to session {id}")

        # Delete analysis results related to these tracks
        deleted_analysis = db.query(AnalysisResult).filter(AnalysisResult.track_id.in_(track_ids)).delete(synchronize_session=False)
        print(f"Deleted {deleted_analysis} analysis results linked to session {id}")

        # Delete tracks themselves
        deleted_tracks = db.query(Track).filter(Track.session_id == id).delete(synchronize_session=False)
        print(f"Deleted {deleted_tracks} tracks linked to session {id}")

    # Finally delete the session itself
    db.delete(session)
    db.commit()

    return {"message": f"Session and all related tracks, analysis, and chats deleted"}


@router.post("/create")
def create_session(
    session_name: str = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
        Create a new session.

        Args:
            session_name (str): Name of the new session.
            user_id (int): ID of the user creating the session.
            db (Session): Database session dependency.

        Returns:
            dict: The ID and name of the newly created session.
        """
    session_id = str(uuid.uuid4())
    new_session = UserSession(
        id=session_id,
        session_name=session_name,
        user_id=user_id
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "id": new_session.id,
        "session_name": new_session.session_name
    }