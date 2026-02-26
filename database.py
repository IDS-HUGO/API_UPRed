from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Crear engine de SQLAlchemy para MySQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20
)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependency para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
