from datasets import load_dataset
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import Annotation, SessionLocal, init_db

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

dataset = load_dataset("MohammadGholizadeh", split="dev[:1%]")

init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/next")
def get_next():
    db = SessionLocal()

    for sample in dataset:
        existing = db.query(Annotation).filter_by(dataset_id=str(sample["id"])).first()
        if not existing:
            return {
                "id": sample["id"],
                "audio": sample["audio"]["array"].tolist(),
                "label": sample["text"],
            }

    return {"done": True}


@app.post("/submit")
async def submit(data: dict):
    db = SessionLocal()

    ann = Annotation(dataset_id=str(data["id"]), label=data["label"], validated=True)
    db.add(ann)
    db.commit()

    return {"status": "ok"}
