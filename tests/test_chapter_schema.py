import json
from pathlib import Path


def test_data_chapters_json_contract():
    path = Path("data/chapters.json")
    assert path.exists(), "Expected data/chapters.json to exist"

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"

    chapters = payload["chapters"]
    assert isinstance(chapters, list)
    assert len(chapters) == 18

    keys = [entry["key"] for entry in chapters]
    assert keys == [str(i) for i in range(1, 19)]

    for entry in chapters:
        assert set(["key", "module", "class", "title"]).issubset(entry.keys())
        assert entry["module"].startswith("chapters.ch")
        assert entry["class"].startswith("Chapter")
