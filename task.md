# Load Balancer — Task Tracking

Builds on: https://github.com/DarynOngera/load_balancer

## Phase 0 — Foundation Cleanup

### Task 0.1 — Split the Monolith
- [x] Create `config.py` with env-based configuration
- [x] Extract `ConsistentHashMap` into `consistent_hash.py`
- [x] Extract Docker management into `docker_manager.py`
- [x] Extract request forwarding into `router.py`
- [x] Create `app.py` as Flask entry point with route registration

### Task 0.2 — Externalize Configuration
- [x] Move hardcoded values to env vars with defaults in `config.py`

### Task 0.3 — Add Request Timeout
- [x] Add `timeout=REQUEST_TIMEOUT` to forwarding call
- [x] Return 504 JSON error on `requests.exceptions.Timeout`

---

## Restructure — src/ Layout + aiohttp

- [x] Scaffold `src/load_balancer/` layout with `pyproject.toml`
- [x] `config.py` — Pydantic Settings schema
- [x] `core/interface.py` — LoadBalancingStrategy ABC
- [x] `core/consistent_hash.py` — ConsistentHash with SHA1 (deterministic)
- [x] `core/round_robin.py` — RoundRobin strategy
- [x] `network/server.py` — aiohttp web app with `/rep`, `/add`, `/rm`, `/{path}`
- [x] `network/proxy.py` — ProxyClient (async forwarding via aiohttp)
- [x] `health/state.py` — ServerPool + ServerStatus enum
- [x] `health/checker.py` — Async health check loop
- [x] `docker/manager.py` — Decoupled DockerManager
- [x] `main.py` + `__main__.py` — Coordinator wiring
- [x] Update Dockerfile (Python 3.11 + pip install .)
- [x] Update docker-compose.yml (context: repo root)
- [x] Verify build, startup, and all endpoints
- [x] Remove old Flask-based files

### Tests
- [x] `tests/conftest.py` — shared fixtures
- [x] `tests/test_config.py` — default settings test
- [x] `tests/test_core/test_consistent_hash.py` — pure algorithm tests
- [x] `tests/test_core/test_round_robin.py` — round-robin tests

---

## Future Phases

### Phase 1 — Correct Consistent Hashing
- [x] Tune and verify virtual nodes (default: 9→100, total_slots: 512→10000)
- [x] Hash real requests (sticky sessions via client_ip, fallback to req_id)
  - [x] `hashing_mode` param on strategy ("sticky"|"random")
  - [x] `client_ip` propagated: server.py → proxy.py → state.py → strategy

### Phase 2 — Real Reverse Proxy
- [x] Forward every HTTP method (add_route("*", ...) already handles all)
- [x] Forward headers, body, query params (query string appended in server.py:122)
- [x] Preserve real responses (not forced JSON) (proxy returns raw: body, status, headers)

### Phase 3 — Failure Handling
- [x] Retry on different backend (`exclude` param through strategy→state→proxy chain)
- [x] Exponential backoff (`_backoff_delay` with `base * 2^attempt`, capped at `retry_max_delay`)
- [x] Automatic recovery (health checker already marks healthy; added exponential backoff per server)
  - [x] `exclude` param on `select_server()` and `get_server()` — strategies skip excluded servers
  - [x] Proxy retry loop: on transport error → mark unhealthy, exclude, backoff, retry (up to `max_retries`)
  - [x] Health checker: track consecutive failures per server, backoff before rechecking unhealthy servers
  - [x] 15 new tests (exclude, backoff, retry loop, exhausted retries, no servers)

### Phase 4 — Concurrency
- [ ] Thread safety (locking) — asyncio handles this, review read/write patterns

### Phase 5 — Observability
- [ ] Structured logging
- [ ] Prometheus metrics
- [ ] Request IDs

### Phase 6 — Load Balancing Algorithms
- [ ] Random, least connections, power of two choices

### Phase 7 — Better Replica Management
- [ ] Graceful draining
- [ ] Container event watcher (optional)

### Phase 8 — Resilience
- [ ] Circuit breaker

### Phase 9 — VPS Production Deployment
- [ ] Gunicorn, socket hardening, TLS, Prometheus/Grafana, stress tests

### Phase 10 — Distributed
- [ ] Redis backend registry
- [ ] Multi-instance LB
- [ ] Compare vs Nginx/HAProxy
