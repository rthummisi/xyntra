from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


class StructuredOutputValidator:
    def validate_required_fields(
        self,
        payload: dict,
        required_fields: list[str],
    ) -> ValidationResult:
        missing = [field for field in required_fields if field not in payload]
        return ValidationResult(valid=not missing, errors=missing)


structured_output_validator = StructuredOutputValidator()
