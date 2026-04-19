#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.semantic_cache_service import semantic_cache_service


async def main() -> None:
    updated = await semantic_cache_service.backfill_missing_embeddings()
    print(f"Backfilled semantic cache embeddings for {updated} row(s).")


if __name__ == "__main__":
    asyncio.run(main())
