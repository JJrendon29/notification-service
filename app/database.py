from sqlmodel import create_engine, Session, SQLModel
from app.config import settings

engine = create_engine(
    settings.database_url.replace("postgresql://", "postgresql+psycopg2://")
)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
