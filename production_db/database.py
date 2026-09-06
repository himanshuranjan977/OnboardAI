"""Optional SQLAlchemy production persistence adapter.

The prototype keeps SQLite as its default for compatibility. Set
DATABASE_URL=postgresql+psycopg://... and use this adapter during production
migration. The domain/runtime contract remains independent of the DB engine.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

def build_engine():
    url=os.getenv("DATABASE_URL","sqlite:///./onboardai.db")
    kwargs={"connect_args":{"check_same_thread":False}} if url.startswith("sqlite") else {}
    return create_engine(url,pool_pre_ping=True,future=True,**kwargs)

engine=build_engine()
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False,expire_on_commit=False)

def init_production_schema():
    from .models import import_models
    import_models()
    Base.metadata.create_all(engine)
