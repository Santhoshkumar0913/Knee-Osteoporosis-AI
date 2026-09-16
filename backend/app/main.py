from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, patients, analyses
from app.core.config import settings

app = FastAPI(
    title="Knee Osteoporosis AI",
    description="AI-assisted screening using knee X-ray images and patient clinical information",
    version="1.0.0"
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    from app.db.database import engine, Base
    Base.metadata.create_all(bind=engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(analyses.router, prefix="/api/analyses", tags=["analyses"])

@app.get("/")
async def root():
    return {
        "message": "Knee Osteoporosis AI API",
        "version": "1.0.0",
        "status": "running"
    }
