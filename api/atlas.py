from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/atlas")
@app.get("/")
async def atlas():
    return {
        "status": "coming_soon",
        "platform": "DreamXV AI Studio",
        "feature": "DreamXV Atlas",
        "description": "Explore worlds, ideas, lore, and inspiration. Coming Soon."
    }
