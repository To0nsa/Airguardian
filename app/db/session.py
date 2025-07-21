from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create a SQLAlchemy Engine connected to the PostgreSQL database.
# `settings.database_url` is loaded from environment variables (.env)
# `pool_pre_ping=True` ensures that connections are validated before use
# to avoid using stale connections from the pool.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Create a configured "SessionLocal" class that will serve as a factory
# for database session objects. These sessions will:
# - Not autocommit transactions (must explicitly call commit())
# - Not autoflush pending changes until commit/flush is called
# - Be bound to the above engine (i.e., connected to the database)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI endpoints to get a database session.
# Usage: Include `db: Session = Depends(get_db)` in route handlers.
# It yields a session, and ensures it is closed properly after use,
# whether the request succeeds or fails.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
