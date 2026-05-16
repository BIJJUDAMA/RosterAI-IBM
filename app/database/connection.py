import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv(override=True)

# PostgreSQL Configuration
PG_USER = os.getenv("POSTGRES_USER", "postgres").strip()
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password").strip()
PG_HOST = "127.0.0.1"
PG_PORT = "5433" 
PG_DB = os.getenv("POSTGRES_DB", "roster").strip()

DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

import time
from sqlalchemy.exc import OperationalError

# Initializes the database and ensures pgvector extension is enabled with retries
def init_db():
   
    max_retries = 5
    retry_delay = 2
    
    from sqlalchemy import inspect
    from app.logging_config import logger
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                # Check and Enable pgvector
                logger.info("[yellow]Checking for pgvector extension...[/yellow]")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("[bold green]✓ pgvector extension is loaded and active.[/bold green]")

            # Create all tables defined in models.py
            logger.info("[yellow]Creating database schema...[/yellow]")
            from .models import Candidate, Project # Explicit import for metadata registration
            Base.metadata.create_all(bind=engine)
            logger.info("[bold green]✓ Schema created successfully.[/bold green]")
            
            # Optimization: Create HNSW Indexes for Vector Search
            logger.info("[yellow]Optimizing vector indices with HNSW...[/yellow]")
            with engine.connect() as conn:
                # Candidates HNSW
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_candidates_embedding_hnsw 
                    ON candidates USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                """))
                # Projects HNSW
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_projects_embedding_hnsw 
                    ON projects USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                """))
                conn.commit()
            logger.info("[bold green]✓ HNSW indices active (Memory-efficient search enabled).[/bold green]")
            
            # Verify tables after creation
            inspector = inspect(engine)
            final_tables = inspector.get_table_names()
            logger.info(f"[bold green]✓ Database initialized. Current tables: {', '.join(final_tables)}[/bold green]")
            return # Success
        except OperationalError as e:
            logger.error(f"[red]Database connection attempt {attempt + 1} failed: {e}[/red]")

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2 
                continue
            else:
                raise e

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
