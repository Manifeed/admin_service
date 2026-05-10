from __future__ import annotations

import json
from pathlib import Path

from app.services.rss_sync_service import _list_catalog_company_names


def test_list_catalog_company_names_uses_json_company_field(tmp_path: Path) -> None:
    catalog_dir = tmp_path / "json"
    catalog_dir.mkdir()
    (catalog_dir / "Liberation.json").write_text(
        json.dumps(
            {
                "company": "Libération",
                "host": "www.liberation.fr",
                "img": "Liberation.svg",
                "country": "fr",
                "fetchprotection": 1,
                "feeds": [],
            }
        ),
        encoding="utf-8",
    )

    company_names = _list_catalog_company_names(catalog_dir)

    assert "Libération" in company_names
    assert "Liberation" not in company_names
