"""
Main entry point for the ZoundZcope FastAPI application.

This module:
    - Configures the FastAPI app, CORS, static file serving, and templates.
    - Registers API routers for file upload, chat, RAG features, token tracking,
      sessions, tracks, and export functionality.
    - Initializes the database schema.
    - Serves HTML frontend pages.
    - Runs a background cleanup task to remove old uploads.

Routes:
    GET /                    - Render the main index page.
    GET /info.html           - Render the info page.
    GET /feedback_history.html - Render the feedback history page.

Static Mounts:
    /static  → Frontend static assets.
    /uploads → Uploaded audio files.

Background Tasks:
    periodic_cleanup_task(): Removes old uploaded files twice daily.

Dependencies:
    - FastAPI, Jinja2, SQLAlchemy, CORSMiddleware.
    - Routers: upload, chat, rag, tokens, sessions, tracks, export.
    - Cleanup utility for old uploads.
"""
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, chat, sessions, tracks, export
from app.database import Base, engine
from app.cleanup import cleanup_old_uploads
from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from app.routers import rag
from app.routers import tokens

from dotenv import load_dotenv
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Application lifespan context manager.

        Starts a periodic cleanup task on application startup
        and ensures it is cancelled on shutdown.

        Args:
            app (FastAPI): The running FastAPI application instance.
        """
    task = asyncio.create_task(periodic_cleanup_task())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="ZoundZcope API", lifespan=lifespan)

logger = logging.getLogger("uvicorn.error")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend-html", "static")

UPLOAD_DIR = os.path.join(BASE_DIR, "backend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


#/================/#
# import for frontend html
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse


Base.metadata.create_all(bind=engine)

#/=====config for frontend-html======/#
# Serve static files like your logo

# Jinja2 template support
templates = Jinja2Templates(directory="../frontend-html/templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(rag.router, prefix="/chat", tags=["RAG"])
app.include_router(tokens.router)
app.include_router(sessions.router)
app.include_router(tracks.router, prefix="/tracks", tags=["Tracks"])
app.include_router(export.router, prefix="/export", tags=["Export"])

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    """
        Render the main index page.

        - Lists uploaded audio files in the uploads directory.
        - Passes the latest uploaded track (if any) to the template.

        Args:
            request (Request): FastAPI request object.

        Returns:
            TemplateResponse: Rendered `index.html` with track context.
        """
    # Look for files in the upload directory
    try:
        files = sorted(
            [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(('.mp3', '.wav', '.flac'))],
            key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)),
            reverse=True
        )
        latest_file = files[0] if files else None
    except Exception as e:
        # print("Error reading uploads:", e)
        latest_file = None

    track_path = f"/uploads/{latest_file}" if latest_file else None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "track_path": track_path
    })


@app.get("/info.html", response_class=HTMLResponse)
async def serve_info(request: Request):
    """
        Render the info page.

        Args:
            request (Request): FastAPI request object.

        Returns:
            TemplateResponse: Rendered `info.html`.
        """
    return templates.TemplateResponse("info.html", {"request": request})


@app.get("/feedback_history.html", response_class=HTMLResponse)
async def serve_feedback_history(request: Request):
    """
        Render the feedback history page.

        Args:
            request (Request): FastAPI request object.

        Returns:
            TemplateResponse: Rendered `feedback_history.html`.
        """
    return templates.TemplateResponse("feedback_history.html", {"request": request})


async def periodic_cleanup_task():
    """
        Background task to periodically clean up old uploaded files.

        Runs every 12 hours and logs actions or errors.
        """
    while True:
        try:
            logger.info("Running periodic cleanup task...")
            cleanup_old_uploads()
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")
        await asyncio.sleep(12 * 60 * 60)  # Run twice daily


@app.on_event("startup")
async def startup_event():
    """
        FastAPI startup event handler.

        Starts the periodic cleanup task in the background.
        """
    asyncio.create_task(periodic_cleanup_task())


