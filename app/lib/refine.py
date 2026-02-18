from typing import Optional

from datasets import Dataset
from sqlalchemy.orm import Session

from app.services.database import Annotation, SessionLocal
from app.services.dataset import load


def get_valid_indices(db: Session):
    return [
        i
        for i, in db.query(
            Annotation.id,
        )
        .filter(
            Annotation.validated == True,
        )
        .all()
    ]


def make_map(db: Session):
    def map(batch):
        indices = batch["index"]

        rows = (
            db.query(
                Annotation.id,
                Annotation.label,
            )
            .filter(Annotation.id.in_(indices))
            .all()
        )

        id_to_label = {row.id: row.label for row in rows}

        batch["text"] = [
            id_to_label[idx] for idx in indices  # Or .get; it fails fast now.
        ]

        return batch

    return map


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
            .select(
                get_valid_indices(session),
            )
            .map(
                make_map(session),
                batched=True,
                input_columns=["index"],
            )
        )
