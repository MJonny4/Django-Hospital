from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# Database configuration
DATABASE_URL = "mysql+pymysql://mjonny4:mjonny4@localhost:3306/hospital?charset=utf8mb4"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # This will log all SQL queries - useful for debugging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Refresh connections every 5 minutes
    connect_args={"charset": "utf8mb4"}  # Ensure UTF-8 encoding for special characters
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection
async def test_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {"status": "connected", "result": result.fetchone()[0]}
    except Exception as e:
        return {"status": "failed", "error": str(e)}