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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # print("Registered routes:")
    # for route in app.routes:
    #     if isinstance(route, APIRoute):
    #         print(route.path, route.methods)
    #     else:
    #         print(route.path, "(mount or other)")

    # Start your periodic cleanup task here:
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
# print("Chat router included")
app.include_router(sessions.router)
app.include_router(tracks.router, prefix="/tracks", tags=["Tracks"])
app.include_router(export.router, prefix="/export", tags=["Export"])

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
# print("Connected to DB at:", engine.url)



@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
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
    return templates.TemplateResponse("info.html", {"request": request})


@app.get("/feedback_history.html", response_class=HTMLResponse)
async def serve_feedback_history(request: Request):
    return templates.TemplateResponse("feedback_history.html", {"request": request})



async def periodic_cleanup_task():
    while True:
        try:
            logger.info("Running periodic cleanup task...")
            cleanup_old_uploads()
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")
        await asyncio.sleep(12 * 60 * 60)  # Run twice daily

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup_task())


