from fastapi import FastAPI
from app.routers import upload, chat, sessions, tracks
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from dotenv import load_dotenv
load_dotenv()


Base.metadata.create_all(bind=engine)


app = FastAPI(title="ZoundZcope API")

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