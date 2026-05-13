import compileall
from pathlib import Path


def test_admin_service_sources_compile() -> None:
    root = Path(__file__).resolve().parents[1]
    assert compileall.compile_dir(root / "app", quiet=1)
    assert compileall.compile_file(root / "app" / "main.py", quiet=1)
