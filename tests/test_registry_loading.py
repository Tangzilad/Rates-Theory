import importlib
import json
from pathlib import Path


def test_chapters_1_to_18_import_and_register_from_contract():
    payload = json.loads(Path("data/chapters.json").read_text(encoding="utf-8"))
    chapters = payload["chapters"]
    assert [entry["key"] for entry in chapters] == [str(i) for i in range(1, 19)]

    registry = {}
    for entry in chapters:
        module = importlib.import_module(entry["module"])
        chapter_class = getattr(module, entry["class"])
        registry[entry["key"]] = chapter_class

    assert sorted(int(key) for key in registry.keys()) == list(range(1, 19))


def test_chapters_package_registry_builds_without_import_errors():
    chapters_pkg = importlib.import_module("chapters")
    registry = chapters_pkg.build_chapter_registry()
    assert registry
    assert "1" in registry
