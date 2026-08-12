from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers import notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Notification Service",
    description="Sistema de notificaciones asincronas con cola Redis y workers ARQ",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(notifications.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
