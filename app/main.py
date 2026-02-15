import os
from typing import TypedDict

import soundfile as sf
import torchcodec
from datasets import load_dataset
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import Annotation, SessionLocal, init_db

AUDIO_DIR = "audio_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/audio", StaticFiles(directory="audio_cache"), name="audio")
templates = Jinja2Templates(directory="app/templates")

dataset = load_dataset("Raziullah/librispeech_small_asr_fine-tune", split="test[:1%]")

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

            audio_path = f"{AUDIO_DIR}/{sample['id']}.wav"

            if not os.path.exists(audio_path):
                sf.write(
                    audio_path,
                    sample["audio"]["array"],
                    sample["audio"]["sampling_rate"],
                )

            return {
                "id": sample["id"],
                "label": sample["text"],
                "audio_url": f"/audio/{sample['id']}.wav",
            }

    return {"done": True}


@app.post("/submit")
async def submit(data: dict):
    db = SessionLocal()

    ann = Annotation(dataset_id=str(data["id"]), label=data["label"], validated=True)
    db.add(ann)
    db.commit()

    return {"status": "ok"}
