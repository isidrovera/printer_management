# server/app/db/session.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from server.app.core.config import settings
import psycopg2
from urllib.parse import urlparse

def create_database():
    url = urlparse(settings.DATABASE_URL)
    database = url.path[1:]
    
    conn = psycopg2.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        port=url.port or 5432
    )
    conn.autocommit = True
    
    cur = conn.cursor()
    try:
        cur.execute(f"CREATE DATABASE {database}")
    except psycopg2.errors.DuplicateDatabase:
        pass
    finally:
        cur.close()
        conn.close()

create_database()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()