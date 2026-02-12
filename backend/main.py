"""
SiPM Tester Station - FastAPI Backend
Main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import motion, camera, measurement, config


# Create FastAPI app
app = FastAPI(
    title="SiPM Tester Station API",
    description="Backend API for controlling SiPM tester station hardware",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include API routers
app.include_router(motion.router)
app.include_router(camera.router)
app.include_router(measurement.router)
app.include_router(config.router)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "service": "SiPM Tester Station API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "motion": "/api/motion",
            "camera": "/api/camera",
            "measurement": "/api/measurement",
            "config": "/api/config"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("SiPM Tester Station - Backend Starting...")
    print("=" * 60)
    print("API Documentation: http://localhost:8000/docs")
    print("API Endpoints:")
    print("  - Motion Control:  /api/motion")
    print("  - Camera:          /api/camera")
    print("  - Measurement:     /api/measurement")
    print("  - Configuration:   /api/config")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
