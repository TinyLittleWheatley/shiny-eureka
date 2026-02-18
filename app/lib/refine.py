from typing import Optional

from datasets import Dataset

from app.services.database import Annotation, SessionLocal
from app.services.dataset import load


def filter(indices):
    db = SessionLocal()

    valid_indices = {
        i
        for i, in db.query(
            Annotation.id,
        )
        .filter(
            Annotation.validated == True,
            Annotation.id.in_(indices),
        )
        .all()
    }

    return [index in valid_indices for index in indices]


def map(indices):
    db = SessionLocal()

    rows = (
        db.query(
            Annotation.id,
            Annotation.label,
        )
        .filter(Annotation.id.in_(indices))
        .all()
    )

    id_to_label = {row.id: row.label for row in rows}

    return {
        "text": [id_to_label[idx] for idx in indices]  # Or .get; it fails fast now.
    }


def refine(ds: Optional[Dataset] = None):
    if ds is None:
        ds = load()

    with SessionLocal() as session:  # TODO: Check if it's ok to use one session
        # persist order
        return (
            ds.add_column(
                "index",
                range(len(ds)),  # pyright: ignore[reportArgumentType]
            )
            .filter(
                filter,
                batched=True,
                input_columns=["index"],
            )
            .map(
                map,
                batched=True,
                input_columns=["index"],
            )
        )
