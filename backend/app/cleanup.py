from pathlib import Path
import os
import time
import logging
from app.database import SessionLocal
from app.models import Track

logger = logging.getLogger("cleanup")

BASE_DIR = Path(os.getcwd()).parent
UPLOAD_FOLDER = BASE_DIR / "backend" / "uploads"
RMS_ANALYSIS_FOLDER = BASE_DIR / "frontend-html" / "static" / "analysis"
MAX_FILE_AGE_SECONDS = 24 * 60 * 60

def cleanup_old_uploads():
    logger.info("Starting cleanup of old uploads...")
    print("Current working dir:", os.getcwd())
    print("BASE_DIR:", BASE_DIR)
    print("UPLOAD_FOLDER:", UPLOAD_FOLDER)
    print("RMS_ANALYSIS_FOLDER:", RMS_ANALYSIS_FOLDER)
    now = time.time()
    db = SessionLocal()
    try:
        # Delete old audio files tracked in DB
        old_tracks = db.query(Track).all()
        for track in old_tracks:
            file_path = track.file_path
            if file_path and os.path.exists(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > MAX_FILE_AGE_SECONDS:
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted old track file: {file_path}")

                        # Also delete associated RMS file if exists
                        basename = os.path.basename(file_path)
                        rms_filename = f"{basename}_rms.json"
                        rms_file_path = RMS_ANALYSIS_FOLDER / rms_filename
                        if rms_file_path.exists():
                            try:
                                rms_file_path.unlink()
                                logger.info(f"Deleted RMS file: {rms_file_path}")
                            except Exception as e:
                                logger.error(f"Error deleting RMS file {rms_file_path}: {e}")

                    except Exception as e:
                        logger.error(f"Error deleting files for {file_path}: {e}")

        # Now delete ALL old RMS JSON files in the RMS_ANALYSIS_FOLDER (cleanup orphan RMS files)
        for rms_file in RMS_ANALYSIS_FOLDER.glob("*.json"):
            file_age = now - rms_file.stat().st_mtime
            if file_age > MAX_FILE_AGE_SECONDS:
                try:
                    rms_file.unlink()
                    logger.info(f"Deleted orphan RMS JSON file: {rms_file}")
                except Exception as e:
                    logger.error(f"Error deleting orphan RMS file {rms_file}: {e}")

    finally:
        db.close()
    logger.info("Cleanup finished.")
