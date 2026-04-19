from __future__ import annotations

from providers.base.multimodal import normalize_attachments


def test_normalize_attachments_applies_defaults_and_preserves_metadata() -> None:
    normalized = normalize_attachments(
        [
            {
                "kind": "image",
                "media_type": "image/png",
                "content": "base64-data",
                "metadata": {"width": 100},
            },
            {
                "content": "raw-bytes",
            },
        ]
    )

    assert normalized[0].kind == "image"
    assert normalized[0].media_type == "image/png"
    assert normalized[0].metadata["width"] == 100
    assert normalized[1].kind == "file"
    assert normalized[1].media_type == "application/octet-stream"
