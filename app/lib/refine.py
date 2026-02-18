from typing import Optional

from datasets import Dataset
from sqlalchemy.orm import Session

from app.services.database import Annotation, SessionLocal
from app.services.dataset import load


def make_filter(db: Session):
    def filter(indices):
        valid_ids = (
            db.query(Annotation.id)
            .filter(
                Annotation.id.in_(indices),
                Annotation.validated.is_(True),
            )
            .all()
        )

        return [idx in valid_ids for idx in indices]

    return filter


def make_map(db: Session):
    def map(batch, indices):
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
        ds.filter(
            make_filter(session),
            with_indices=True,
            batched=True,
            input_columns=["text"],
        )

        ds.map(
            make_map(session),
            batched=True,
            with_indices=True,
            input_columns=[],
        )

    return ds
