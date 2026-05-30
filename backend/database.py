import os
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

# Find the root directory and load .env file
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(workspace_dir, ".env")
load_dotenv(dotenv_path)

# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./drivelegal.db")

# Create Database Engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False} # Required for SQLite with multithreaded FastAPI
    )
else:
    engine = create_engine(DATABASE_URL)

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
