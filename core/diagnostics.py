from __future__ import annotations

from typing import Any


class ChapterValidationError(ValueError):
    """Raised when upstream chapter state does not satisfy expected schema."""


def validate_dataclass_instance(payload: Any, expected_type: type) -> list[str]:
    if not isinstance(payload, expected_type):
        return [f"Expected {expected_type.__name__}, received {type(payload).__name__}."]
    return []


def validate_boundary(
    chapter_id: str,
    required_inputs: dict[str, type],
    upstream_exports: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for required_chapter, expected_type in required_inputs.items():
        upstream_payload = upstream_exports.get(required_chapter)
        if upstream_payload is None:
            errors.append(
                f"Chapter {chapter_id} requires exports from chapter {required_chapter} before rendering interactive lab."
            )
            continue
        errors.extend(validate_dataclass_instance(upstream_payload, expected_type))
    return errors
