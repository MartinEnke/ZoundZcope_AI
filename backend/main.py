from fastapi import FastAPI
from app.routers import upload, chat, sessions, tracks
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from dotenv import load_dotenv
load_dotenv()

#/================/#
# import for frontend html
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse


Base.metadata.create_all(bind=engine)


app = FastAPI(title="ZoundZcope API")

#/================/#
# config for frontend-html
# Serve static files like your logo
app.mount("/static", StaticFiles(directory="../frontend-html/static"), name="static")
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
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(tracks.router, prefix="/tracks", tags=["Tracks"])



@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})