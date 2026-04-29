from sqlalchemy import text
from sqlalchemy.orm import Session


def count_users(db: Session) -> int:
    return int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM users
                """
            )
        ).scalar_one()
    )


def count_connected_users(db: Session) -> int:
    return int(
        db.execute(
            text(
                """
                SELECT COUNT(DISTINCT user_id)
                FROM user_sessions
                WHERE revoked_at IS NULL
                    AND expires_at > now()
                """
            )
        ).scalar_one()
    )
