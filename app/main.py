from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import Base, engine
from app import models  # noqa: F401
from app.api import tasks, dependencies

app = FastAPI(title="TaskFlow Pro")

Base.metadata.create_all(bind=engine)

app.include_router(tasks.router)
app.include_router(dependencies.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def board_page(request: Request):
    return templates.TemplateResponse(request, "board.html", {})
