from src.chapters.registry import (
    CHAPTER_DEPENDENCIES,
    build_chapter_registry,
    validate_chapter_dependencies,
)


def test_registry_dependencies_validate_cleanly():
    result = validate_chapter_dependencies(build_chapter_registry())
    assert result.has_errors is False


def test_validation_flags_missing_required_chapter():
    registry = build_chapter_registry()
    registry.pop("1")

    result = validate_chapter_dependencies(registry)

    assert result.has_errors is True
    assert any("Required chapter 1 is missing" in issue.message for issue in result.issues)


def test_validation_flags_unresolved_export_key():
    registry = build_chapter_registry()
    dependency_map = dict(CHAPTER_DEPENDENCIES)
    dependency_map["2"] = {"1": ["does_not_exist"]}

    result = validate_chapter_dependencies(registry, dependency_map=dependency_map)

    assert result.has_errors is True
    assert any("does_not_exist" in issue.message for issue in result.issues)
