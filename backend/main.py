import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.tasks.scheduler import start_scheduler
from backend.routers import midi, scrape, agent as agent_router

logging.basicConfig(level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(title="midi-haul", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(midi.router, prefix="/api/midi")
app.include_router(scrape.router, prefix="/api/scrape")
app.include_router(agent_router.router, prefix="/api/agent")

# Serve built React app — only mount if the dist directory exists
import os
if os.path.isdir("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
