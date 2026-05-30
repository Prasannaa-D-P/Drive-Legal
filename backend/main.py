import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import engine, Base
from backend.routers import rules, geo, challan, chat, general

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="DriveLegal India API",
    description="Backend API system for traffic violations, compounding calculations, geofencing, and RTO vehicle challan checks.",
    version="1.0.0"
)

# CORS Configuration (allows frontend to call API even if served elsewhere)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(rules.router, prefix="/api")
app.include_router(geo.router, prefix="/api")
app.include_router(challan.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(general.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "drivelegal-backend"}

# Mount frontend static files
# Make sure the frontend files exist in the directory path
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
www_dir = os.path.join(workspace_dir, "www")
app.mount("/", StaticFiles(directory=www_dir, html=True), name="static")

if __name__ == "__main__":
    # Start uvicorn server locally on port 8000
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
