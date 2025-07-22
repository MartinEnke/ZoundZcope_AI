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
        old_tracks = db.query(Track).all()
        for track in old_tracks:
            file_path = track.file_path
            if file_path and os.path.exists(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > MAX_FILE_AGE_SECONDS:
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted old track file: {file_path}")

                        basename = os.path.basename(file_path)
                        rms_filename = f"{basename}_rms.json"
                        rms_file_path = RMS_ANALYSIS_FOLDER / rms_filename
                        print(f"Looking for RMS file at: {rms_file_path}")
                        if rms_file_path.exists():
                            try:
                                rms_file_path.unlink()
                                print(f"Deleted RMS file: {rms_file_path}")
                            except Exception as e:
                                print(f"Error deleting RMS file {rms_file_path}: {e}")
                        else:
                            print(f"RMS file not found at: {rms_file_path}")
                        logger.debug(f"Checking RMS file for deletion: {rms_file_path}")
                        if rms_file_path.exists():
                            rms_file_path.unlink()
                            logger.info(f"Deleted old RMS chunk file: {rms_file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting files for {file_path}: {e}")
    finally:
        db.close()
    logger.info("Cleanup finished.")
