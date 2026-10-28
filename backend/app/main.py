import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.db.database import engine, Base
from backend.app.models.models import *  # Ensure all models registered
from backend.app.api import api_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="YottaFlex AI — Recruitment Management and Analytics System",
    description="End-to-End Enterprise Recruitment Platform with Deterministic Screening, Anomaly Detection, and Audit Traceability.",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core API
app.include_router(api_router)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "YottaFlex Recruitment API",
        "version": "1.0.0",
        "database": "sqlite_connected"
    }

# Mount static frontend directory if exists
frontend_dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
frontend_public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")

if os.path.exists(frontend_dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "docs" or full_path == "openapi.json":
            return None
        file_path = os.path.join(frontend_dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_dir, "index.html"))
elif os.path.exists(frontend_public_dir):
    @app.get("/")
    async def serve_index():
        index_file = os.path.join(frontend_public_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "YottaFlex Recruitment API is running. Visit /docs for Swagger UI."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
