<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-blue.svg" alt="Language">
  <img src="https://img.shields.io/badge/Framework-aiohttp-green.svg" alt="Framework">
  <img src="https://img.shields.io/badge/Platform-Docker-blue.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

# Async Load Balancer

An asynchronous load balancer built with Python and aiohttp, designed to distribute requests across a dynamic pool of Docker-based backend servers using configurable routing strategies.

## Features

- **Multiple Routing Algorithms**: Consistent hashing (with SHA1-based deterministic hashing and virtual nodes) and round-robin, with a pluggable strategy interface
- **Dynamic Scaling**: Add or remove backend servers via API endpoints without downtime
- **Async Proxy**: Non-blocking request forwarding using aiohttp with configurable timeouts
- **Background Health Checks**: Automatic detection of unhealthy backends via periodic `/heartbeat` polling
- **Deterministic Hashing**: SHA1-based server IDs ensure identical ring layout across restarts and multiple load balancer instances
- **Decoupled Docker Management**: Container lifecycle is handled through a dedicated module, keeping the core routing logic IO-free
- **Typed Config**: All parameters configured through environment variables with Pydantic schema validation

## Prerequisites

- Linux (tested on Debian/Ubuntu/Parrot)
- Docker 20.10.23+
- Docker Compose v2.15.1+

## Quick Start

```bash
git clone https://github.com/DarynOngera/load_balancer
cd load_balancer

make build      # Build Docker images (load balancer + server)
make up         # Start the load balancer (initializes N=3 servers)
make logs       # Tail logs
make down       # Stop and remove all containers
```

Once running, the load balancer is available at `http://localhost:5000`.

## API Endpoints

### `GET /rep`
Returns all active backend servers.

```bash
curl http://localhost:5000/rep
# {"N": 3, "replicas": ["server0","server1","server2"], "status": "successful"}
```

### `POST /add`
Scale up by adding servers.

| Payload | Description |
|---------|-------------|
| `{"n": 2}` | Add 2 servers with random names |
| `{"n": 2, "hostnames": ["s10", "s11"]}` | Add 2 servers with specific names |

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"n": 2, "hostnames": ["s10"]}' \
  http://localhost:5000/add
```

### `DELETE /rm`
Scale down by removing servers.

| Payload | Description |
|---------|-------------|
| `{"n": 1}` | Remove 1 random server |
| `{"n": 2, "hostnames": ["server1"]}` | Remove server1 + 1 random server |

```bash
curl -X DELETE -H "Content-Type: application/json" \
  -d '{"n": 1, "hostnames": ["s10"]}' \
  http://localhost:5000/rm
```

### `GET /<path>`
Forward any request path to a backend server chosen by the active routing strategy.

```bash
curl http://localhost:5000/home
# {"message": "Hello from Server: server2", "status": "successful"}
```

## Configuration

All settings are configurable via environment variables (defaults shown):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_IMAGE` | `server-img` | Docker image for backend containers |
| `NETWORK_NAME` | `net1` | Docker network name |
| `INITIAL_REPLICA_COUNT` | `3` | Number of servers on startup |
| `TOTAL_SLOTS` | `512` | Hash ring slot count |
| `NUM_VIRTUAL_SERVERS` | `9` | Virtual nodes per server |
| `REQUEST_TIMEOUT` | `5` | Backend request timeout (seconds) |
| `HEALTH_CHECK_INTERVAL` | `10` | Seconds between health check pings |
| `LB_PORT` | `5000` | Load balancer listen port |

Copy `.env.example` to `.env` and modify as needed.

## Project Layout

```
src/load_balancer/
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

## Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run unit tests
pytest

# Load testing (standalone script, requires aiohttp + matplotlib)
pip install aiohttp matplotlib
python tester.py
```

## Design

- **Async-first**: All I/O runs on `asyncio` via `aiohttp`. No blocking calls in the main loop.
- **Deterministic hashing**: SHA1 replaces Python's `hash()` so the ring layout is identical across restarts and LB instances — a prerequisite for horizontal scaling.
- **Dependency injection**: Strategies, pools, and proxy clients are injected via constructors rather than global singletons, making the core algorithms testable without Docker or networking.
- **Decoupled Docker**: The Docker manager (`docker/manager.py`) is a separate concern. The core routing logic in `core/` has no knowledge of containers.

## Roadmap

Tracked in [`task.md`](task.md) — phases include full reverse proxy (headers, body, all HTTP methods), circuit breaker, Prometheus metrics, graceful draining, Redis-backed shared state for multi-instance operation, and VPS hardening.
