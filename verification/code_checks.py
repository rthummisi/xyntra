from __future__ import annotations

from verification.validators import ValidationResult


class CodePatchValidator:
    def validate_patch(self, patch_text: str) -> ValidationResult:
        if not patch_text.strip():
            return ValidationResult(valid=False, errors=["Patch is empty."])
        if "*** Begin Patch" not in patch_text or "*** End Patch" not in patch_text:
            return ValidationResult(valid=False, errors=["Patch markers missing."])
        return ValidationResult(valid=True)


code_patch_validator = CodePatchValidator()
