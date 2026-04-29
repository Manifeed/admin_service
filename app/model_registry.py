from __future__ import annotations

from importlib import import_module

from sqlalchemy.orm import configure_mappers

_MODEL_MODULES = (
    "app.rss.models.rss_catalog_sync_state_model",
    "app.rss.models.rss_company_model",
    "app.rss.models.rss_feed_model",
    "app.rss.models.rss_feed_runtime_model",
    "app.rss.models.rss_feed_tag_model",
    "app.rss.models.rss_tag_model",
)


def configure_model_registry() -> None:
    for module_name in _MODEL_MODULES:
        import_module(module_name)
    configure_mappers()
