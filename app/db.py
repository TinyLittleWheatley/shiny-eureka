from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:////data/data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String)
    validated = Column(Boolean, default=None)
    last_loaded = Column(DateTime, nullable=False, server_default=func.now())


def init_db():
    Base.metadata.create_all(bind=engine)
