# AGENTS.md — Project Conventions & Commands

## Project
Async load balancer in Python/aiohttp/Docker, evolved via the roadmap in `task.md`.

## Commands
```bash
make build    # docker-compose build
make up       # docker-compose up -d load_balancer
make down     # docker-compose down
make logs     # docker-compose logs -f
pytest        # run unit tests (install dev deps first)
```

## Project Layout
```
src/load_balancer/          # Source root (installed via pyproject.toml)
├── __init__.py
├── __main__.py             # python -m load_balancer
├── main.py                 # Coordinator — wires strategy, server, health, docker
├── config.py               # Pydantic Settings schema
├── core/                   # Pure LB algorithms (no IO, DI-friendly)
│   ├── interface.py        # LoadBalancingStrategy ABC
│   ├── consistent_hash.py  # Consistent hashing with SHA1
│   └── round_robin.py      # Round-robin strategy
├── network/                # Async HTTP server & proxy
│   ├── server.py           # aiohttp web app, routes
│   └── proxy.py            # ProxyClient — forwards requests to backends
├── health/                 # Server state & background checks
│   ├── state.py            # ServerPool, ServerStatus enum
│   └── checker.py          # Async health check loop
└── docker/                 # Docker container management (decoupled)
    └── manager.py          # DockerManager — spawn/remove/init containers
tests/
├── conftest.py
├── test_config.py
└── test_core/
    ├── test_consistent_hash.py
    └── test_round_robin.py
```

## Code Conventions
- **Style**: PEP 8 (Black-compatible). No added comments unless asked.
- **Imports**: Standard lib first, then third-party, then local. One import per line for `from` imports.
- **Types**: 100% type coverage. Use `from __future__ import annotations` for modern syntax.
- **Docstrings**: Google-style for every class, public method, and non-trivial function.
- **Error handling**: Return JSON `{"message": "...", "status": "failure"}` with appropriate HTTP status.
- **Config**: Pydantic `Settings` model in `config.py`. Never hardcode values in logic.
- **Async**: All IO via `asyncio` + `aiohttp`. No blocking calls (`requests`, `time.sleep`) in main loop.
- **DI**: Pass backends, pools, strategies via constructors. No global singletons.
- **Testing**: `pytest` + `pytest-asyncio`. Core algorithms must be pure functions testable without mocking.
- **Testing**: Use `tester.py` (consolidated from the 3 duplicates). Run `python tester.py` for load tests.
- **Logging**: Currently uses `print()`. Structured logging comes in Phase 5.

## Phase Structure
Each phase is tracked in `task.md`. Tasks within a phase are ordered by dependency — complete in order.

## Git
- One commit per task (not per file).
- Commit messages: concise, focus on "why" not "what".
- Never commit unless explicitly asked.
