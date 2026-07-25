from fastapi import FastAPI

app = FastAPI(
    title="Construction Evidence Intelligence Platform API",
    description="Backend API for the CEIP Master's Thesis Project",
    version="0.2.0",
)


@app.get("/", tags=["System"])
def root():
    return {
        "application": "Construction Evidence Intelligence Platform",
        "version": "0.2.0",
        "status": "running",
        "message": "Welcome to the CEIP API",
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
    }