import os
from datetime import datetime, timezone

import soundfile as sf
from datasets import DownloadConfig, load_dataset
from fastapi import FastAPI, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, update
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app import config
from app.db import Annotation, SessionLocal, init_db

os.makedirs(config.AUDIO_DIR, exist_ok=True)

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=config.ASSETS_DIR + "/static"),
    name="static",
)

app.mount(
    "/audio",
    StaticFiles(directory=config.AUDIO_DIR),
    name="audio",
)

templates = Jinja2Templates(directory=config.ASSETS_DIR + "/templates")

dataset = load_dataset(
    config.DS_NAME,
    split=config.DS_SPLIT,
    download_config=DownloadConfig(),
)

init_db()


def get_progress():
    db = SessionLocal()

    progress = (
        db.scalar(
            select(
                func.count(
                    Annotation.id,
                ).filter(Annotation.validated != None)
            )
        )
        or 0
    )

    return round(progress / len(dataset) * 100, 2)


class ProgressHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # call the route handler
        response: Response = await call_next(request)

        response.headers["X-Progress"] = str(get_progress())
        return response


app.add_middleware(ProgressHeaderMiddleware)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "progress": get_progress(),
            "dataset_name": config.DS_NAME,
        },
    )


@app.get("/next")
def get_next():
    db = SessionLocal()

    with db.begin():
        last_seen_id = db.scalar(select(func.max(Annotation.id)))
        if not last_seen_id:
            sample_id = 1
        elif last_seen_id + 1 < len(dataset):
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

            if (
                sample_id is None
            ):  # Let this be an identity check so the addition would immediately fail
                return {"done": True}
            else:
                sample_id += 1

        db.merge(Annotation(id=sample_id, last_loaded=datetime.now(timezone.utc)))

    sample = dataset[sample_id]

    audio_path = f"{config.AUDIO_DIR}/{sample['id']}.wav"

    if not os.path.exists(audio_path):
        sf.write(
            audio_path,
            sample["audio"]["array"],
            sample["audio"]["sampling_rate"],
        )

    return {
        "id": sample_id,
        "label": sample["text"],
        "audio_url": f"/audio/{sample['id']}.wav",
    }


@app.post("/submit")
async def submit(data: dict):
    db = SessionLocal()
    db.execute(
        update(Annotation)
        .where(Annotation.id == data["id"])
        .values(label=data["label"], validated=True)
    )
    db.commit()

    return {"status": "ok"}


@app.post("/skip")
async def skip(data: dict):
    db = SessionLocal()
    db.execute(
        update(Annotation).where(Annotation.id == data["id"]).values(validated=False)
    )
    db.commit()

    return {"status": "ok"}
