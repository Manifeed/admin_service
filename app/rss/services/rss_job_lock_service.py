from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar
from sqlalchemy.orm import Session

from shared_backend.errors.custom_exceptions import JobAlreadyRunningError
from app.rss.domain.job_lock import JobAlreadyRunning, job_lock

_LockedActionReturn = TypeVar("_LockedActionReturn")

def run_locked_rss_action(
    db: Session,
    *,
    lock_name: str,
    lock_error_message: str,
    action: Callable[[], _LockedActionReturn],
) -> _LockedActionReturn:
    try:
        with job_lock(db, lock_name):
            return action()
    except JobAlreadyRunning as exception:
        raise JobAlreadyRunningError(lock_error_message) from exception
