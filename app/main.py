import os
from datetime import datetime, timezone

import soundfile as sf
from datasets import DownloadConfig, load_dataset
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select

from app import config
from app.db import Annotation, SessionLocal, init_db

os.makedirs(config.AUDIO_DIR, exist_ok=True)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/audio", StaticFiles(directory=config.AUDIO_DIR), name="audio")
templates = Jinja2Templates(directory="app/templates")

dataset = load_dataset(
    config.DS_NAME,
    split=config.DS_SPLIT,
    download_config=DownloadConfig(),
)

init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/next")
def get_next():
    db = SessionLocal()

    with db.begin():
        last_seen_id = db.scalar(select(func.max(Annotation.id)))
        if not last_seen_id:
            sample_id = 0
        elif last_seen_id < len(dataset) - 1:
            sample_id = last_seen_id + 1
        else:
            sample_id = db.scalar(
                select(
                    Annotation.id,
                )
                .filter(
                    Annotation.validated == None,
                )
                .order_by(
                    Annotation.last_loaded.asc(),
                )
                .limit(1)
            )

            if sample_id is None:
                return {"done": True}

        db.add(Annotation(id=sample_id, last_loaded=datetime.now(timezone.utc)))

    sample = dataset[sample_id]

    audio_path = f"{config.AUDIO_DIR}/{sample['id']}.wav"

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


@app.post("/submit")
async def submit(data: dict):
    db = SessionLocal()

    ann = Annotation(id=data["id"], label=data["label"], validated=True)
    db.add(ann)
    db.commit()

    return {"status": "ok"}


@app.post("/skip")
async def skip(data: dict):
    db = SessionLocal()

    ann = Annotation(id=data["id"], validated=False)
    db.add(ann)
    db.commit()

    return {"status": "ok"}
