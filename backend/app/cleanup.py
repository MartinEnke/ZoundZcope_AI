from pathlib import Path
import os
import time
import logging
from app.database import SessionLocal
from app.models import Track, AnalysisResult

logger = logging.getLogger("cleanup")

BASE_DIR = Path(os.getcwd()).parent
UPLOAD_FOLDER = BASE_DIR / "backend" / "uploads"
RMS_ANALYSIS_FOLDER = BASE_DIR / "frontend-html" / "static" / "analysis"
MAX_FILE_AGE_SECONDS =  60 # run daily

def cleanup_old_uploads():
    logger.info("Starting cleanup of old uploads...")
    # print("Current working dir:", os.getcwd())
    # print("BASE_DIR:", BASE_DIR)
    # print("UPLOAD_FOLDER:", UPLOAD_FOLDER)
    # print("RMS_ANALYSIS_FOLDER:", RMS_ANALYSIS_FOLDER)
    now = time.time()
    db = SessionLocal()
    try:
        # Delete old audio files tracked in DB and remove their DB records
        old_tracks = db.query(Track).all()
        # print(f"Found {len(old_tracks)} tracks in DB")
        for track in old_tracks:
            file_path_str = track.file_path
            if not file_path_str:
                # print("Track has no file_path, skipping")
                continue

            file_path = Path(file_path_str)
            # print(f"Checking track file path: {file_path}")

            if file_path.exists():
                file_age = now - file_path.stat().st_mtime
                # print(f"File age (seconds): {file_age}")
                if file_age > MAX_FILE_AGE_SECONDS:
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted old track file: {file_path}")

                        # Also delete associated RMS file if exists
                        rms_filename = f"{file_path.name}_rms.json"
                        rms_file_path = RMS_ANALYSIS_FOLDER / rms_filename
                        if rms_file_path.exists():
                            try:
                                rms_file_path.unlink()
                                logger.info(f"Deleted RMS file: {rms_file_path}")
                            except Exception as e:
                                logger.error(f"Error deleting RMS file {rms_file_path}: {e}")

                        # Delete related analysis_results
                        deleted_count = db.query(AnalysisResult).filter(AnalysisResult.track_id == track.id).delete()
                        logger.info(f"Deleted {deleted_count} analysis results for track {track.id}")

                        # Instead of deleting Track, just clear the file_path
                        track.file_path = None
                        db.add(track)  # mark for update

                    except Exception as e:
                        logger.error(f"Error deleting files or DB record for {file_path}: {e}")
            #     else:
            #         print(f"File not old enough to delete: {file_path}")
            # else:
            #     print(f"File path does not exist: {file_path}")

        db.commit()  # Commit deletions after all done

        # Delete all old orphan files in the UPLOAD_FOLDER (files not tracked in DB)
        # print("Checking for orphan files in upload folder...")
        for file_path in UPLOAD_FOLDER.iterdir():
            if file_path.is_file():
                file_age = now - file_path.stat().st_mtime
                # print(f"Orphan file {file_path}, age: {file_age}")
                if file_age > MAX_FILE_AGE_SECONDS:
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted orphan upload file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting orphan upload file {file_path}: {e}")

        # Delete all old RMS JSON files in the RMS_ANALYSIS_FOLDER (cleanup orphan RMS files)
        # print("Checking for orphan RMS JSON files...")
        for rms_file in RMS_ANALYSIS_FOLDER.glob("*.json"):
            file_age = now - rms_file.stat().st_mtime
            # print(f"RMS file {rms_file}, age: {file_age}")
            if file_age > MAX_FILE_AGE_SECONDS:
                try:
                    rms_file.unlink()
                    logger.info(f"Deleted orphan RMS JSON file: {rms_file}")
                except Exception as e:
                    logger.error(f"Error deleting orphan RMS file {rms_file}: {e}")

    finally:
        db.close()
    logger.info("Cleanup finished.")
