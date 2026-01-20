import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError, DBAPIError
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"connect_timeout": settings.DB_CONNECT_TIMEOUT},
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo_pool=settings.DB_ECHO_POOL,
)
logger.info(
    f"Database engine created with pool_size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}"
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError:
        logger.error("Database connection error", exc_info=True)
        raise
    except DBAPIError:
        logger.error("Database API error", exc_info=True)
        raise
    finally:
        db.close()
        logger.debug("Database session closed")

