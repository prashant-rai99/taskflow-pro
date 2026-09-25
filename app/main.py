from fastapi import FastAPI
from app.db import Base, engine
from app import models  # noqa: F401
from app.api import tasks, dependencies

app = FastAPI(title="TaskFlow Pro")

Base.metadata.create_all(bind=engine)

app.include_router(tasks.router)
app.include_router(dependencies.router)


@app.get("/health")
def health():
    return {"status": "ok"}
