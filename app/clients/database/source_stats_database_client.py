from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def count_sources(db: Session) -> int:
    return int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM articles AS article
                """
            )
        ).scalar_one()
        or 0
    )
