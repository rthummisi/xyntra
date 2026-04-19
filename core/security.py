from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel


class APIKeyRecord(BaseModel):
    key_id: str
    token_preview: str
    token_hash: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


class APIKeyManager:
    def create_key(self, *, ttl_days: int = 90) -> tuple[str, APIKeyRecord]:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        key_id = secrets.token_hex(8)
        issued_at = datetime.now(UTC)
        record = APIKeyRecord(
            key_id=key_id,
            token_preview=raw_token[:6],
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(days=ttl_days),
        )
        return raw_token, record

    def verify_key(self, raw_token: str, token_hash: str, expires_at: datetime) -> bool:
        if self.is_expired(expires_at):
            return False
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest() == token_hash

    def verify_record(self, raw_token: str, record: APIKeyRecord) -> bool:
        if record.revoked_at is not None:
            return False
        return self.verify_key(raw_token, record.token_hash, record.expires_at)

    def rotate_key(
        self,
        record: APIKeyRecord,
        *,
        ttl_days: int = 90,
    ) -> tuple[str, APIKeyRecord]:
        rotated_token, rotated_record = self.create_key(ttl_days=ttl_days)
        rotated_record = rotated_record.model_copy(update={"key_id": record.key_id})
        return rotated_token, rotated_record

    def revoke_key(self, record: APIKeyRecord) -> APIKeyRecord:
        return record.model_copy(update={"revoked_at": datetime.now(UTC)})

    @staticmethod
    def is_expired(expires_at: datetime) -> bool:
        return datetime.now(UTC) >= expires_at


api_key_manager = APIKeyManager()
