from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import router
import os

app = FastAPI(
    title="AuraLace DSP API",
    description="Premium Audio Signal Processing Backend",
    version="1.0.0",
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve processed audio files
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

# Routes
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {
        "name": "AuraLace DSP API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }