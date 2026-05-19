from __future__ import annotations

import os
import re

import httpx

_RSS_WORKER_GITHUB_REPO_ENV = "RSS_WORKER_GITHUB_REPOSITORY"
_DEFAULT_REPO = "Manifeed/workers"
_TAG_VERSION = re.compile(r"^v?(\d+\.\d+\.\d+)")


def resolve_active_rss_worker_version() -> str | None:
    repo = os.getenv(_RSS_WORKER_GITHUB_REPO_ENV, _DEFAULT_REPO).strip() or _DEFAULT_REPO
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        response = httpx.get(url, timeout=10.0, headers={"User-Agent": "manifeed-admin-service"})
        response.raise_for_status()
    except (httpx.HTTPError, ValueError):
        return None
    tag = str(response.json().get("tag_name", "")).strip()
    match = _TAG_VERSION.match(tag)
    if match is None:
        return None
    return match.group(1)
