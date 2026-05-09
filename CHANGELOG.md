# Changelog — Xyntra

All notable changes to this project are documented here.
Versioning follows [Semantic Versioning](https://semver.org): MAJOR.MINOR.PATCH.

---

## [1.0.0] — 2026-05-08

### Added — Contract Validation Service + Test Suite
- `services/contract_validation_service.py`: full contract validation logic
- `tests/unit/test_contract_validation.py`: unit test coverage for validation service
- `docs/RELEASE_1_0_0.md`: release documentation

**Why this matters:** Contract validation is the core trust primitive in Xyntra. Having it tested and documented is the v1.0 quality bar.

---

## [0.4.0] — 2026-04

### Added — Control Plane + Routing Simulator
- Full control plane architecture shipped
- Routing policy simulator UI (`ui/src/pages/site/SiteTryXyntra.tsx`)
- V2 moats and differentiators strategy matrix
- 150-task build list formalised in AGENTS.md
- 23 frontend surfaces added to build plan

**Why this matters:** The control plane is the operational backbone — routing policies determine how agents are dispatched. The simulator lets prospects test routing logic before signing up.

---

## [0.2.0] — 2026-03

### Added — Core Platform
- FastAPI backend with full API layer
- CLI (`xyntra_cli.py`)
- Alembic database migrations
- Docker deployment configuration

---

## [0.1.0] — 2026-02

### Initial Release
- Project scaffolding
- Core specification and contract
- Initial architecture design
