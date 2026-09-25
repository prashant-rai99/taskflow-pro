from fastapi import FastAPI
from app.db import Base, engine
from app import models  # noqa: F401 -- registers models with Base

app = FastAPI(title="TaskFlow Pro")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
