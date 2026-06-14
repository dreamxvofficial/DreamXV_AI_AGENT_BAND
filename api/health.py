from fastapi import FastAPI
import os
import sys

# Ensure backend package can be imported by adding the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings

app = FastAPI()

@app.get("/api/health")
@app.get("/")
async def health():
    return {
        "status": "ok",
        "platform": "DreamXV AI Studio"
    }
