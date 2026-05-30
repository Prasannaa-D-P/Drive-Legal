import os
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

# Database file location in workspace
DATABASE_URL = "sqlite:///./drivelegal.db"

# Create Database Engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} # Required for SQLite with multithreaded FastAPI
)

# Session Local factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()

# Dependency helper to get DB session in FastAPI routers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
