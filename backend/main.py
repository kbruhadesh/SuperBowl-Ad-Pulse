"""
SuperBowl Ad Pulse — Main FastAPI Application.

Entry point for the backend API.
This file does minimal setup and imports routes from the api module.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .db.database import init_db

# Initialize database on startup
init_db()

# Create FastAPI app
app = FastAPI(
    title="SuperBowl Ad Pulse API",
    description="Real-time sports video analysis and ad generation pipeline",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "SuperBowl Ad Pulse API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
