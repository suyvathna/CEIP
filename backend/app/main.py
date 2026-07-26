from fastapi import FastAPI
from sqlalchemy import text

from app.api import api_router
from app.db.database import engine

app = FastAPI(
    title="Construction Evidence Intelligence Platform API",
    version="0.3.0",
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "application": "CEIP",
        "version": "0.3.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/database")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.scalar()

    return {
        "database": "connected",
        "postgres_version": version,
    }