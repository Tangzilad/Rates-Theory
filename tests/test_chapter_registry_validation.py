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


def test_chapters_7_to_12_dependency_exports_are_present() -> None:
    registry = build_chapter_registry()
    result = validate_chapter_dependencies(registry)

    targeted_chapters = {str(i) for i in range(7, 13)}
    targeted_errors = [
        issue
        for issue in result.issues
        if issue.severity == "error" and issue.chapter in targeted_chapters
    ]
    assert targeted_errors == []

    for chapter_key in map(str, range(7, 13)):
        for provider_key, required_keys in CHAPTER_DEPENDENCIES[chapter_key].items():
            provider_exports = result.exports_by_chapter[provider_key]
            assert set(required_keys).issubset(provider_exports)


def test_chapters_7_to_12_dependencies_are_chronological() -> None:
    for chapter_key in map(str, range(7, 13)):
        for provider_key in CHAPTER_DEPENDENCIES[chapter_key]:
            assert int(provider_key) < int(chapter_key)


def test_registry_builds_all_18_chapters_without_missing_keys_regression() -> None:
    registry = build_chapter_registry()
    assert list(registry.keys()) == [str(i) for i in range(1, 19)]

    result = validate_chapter_dependencies(registry)
    missing_key_errors = [issue for issue in result.issues if "Required exports" in issue.message]
    assert missing_key_errors == []
