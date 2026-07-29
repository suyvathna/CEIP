from fastapi import FastAPI     #responsible for creating the FastAPI application instance
from fastapi.middleware.cors import CORSMiddleware  #responsible for allowing the frontend (different origin) to call this API
from sqlalchemy import text     #responsible for executing raw SQL queries

from app.api import api_router  #responsible for including the API router that contains all the API endpoints
from app.db.database import engine  #responsible for creating a connection to the database using SQLAlchemy's engine

app = FastAPI(
    title="Construction Evidence Intelligence Platform API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite's default dev server port
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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