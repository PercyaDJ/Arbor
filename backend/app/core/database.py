"""
ARBOR - Configuration de la base de données (SQLAlchemy sync/hybride).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy ARBOR."""
    pass


# Initialisation paresseuse du moteur et de la session factory
_engine = None
_session_factory = None


def get_engine():
    """Crée ou retourne le moteur SQLAlchemy (singleton paresseux)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory():
    """Retourne la session factory (singleton paresseux)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), class_=Session, expire_on_commit=False
        )
    return _session_factory


def get_db():
    """
    Dépendance FastAPI : fournit une session DB par requête.
    Usage : db: Session = Depends(get_db)
    """
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
