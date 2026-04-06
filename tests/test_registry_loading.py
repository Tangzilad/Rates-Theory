import importlib

from chapters import build_chapter_registry, validate_chapter_dependencies


def test_chapters_1_to_18_import_and_register():
    registry = build_chapter_registry()
    assert sorted(int(k) for k in registry.keys()) == list(range(1, 19))

    for i in range(1, 19):
        module = importlib.import_module(f"chapters.ch{i:02d}")
        chapter_class = getattr(module, f"Chapter{i:02d}")
        assert registry[str(i)].__class__ is chapter_class


def test_registry_dependency_validation_reports_structured_result():
    result = validate_chapter_dependencies(build_chapter_registry())
    assert isinstance(result.issues, list)
    assert isinstance(result.exports_by_chapter, dict)
