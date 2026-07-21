from __future__ import annotations

from load_balancer.core.round_robin import RoundRobinStrategy
from load_balancer.health.state import ServerPool


def test_get_server_does_not_return_unhealthy() -> None:
    pool = ServerPool(strategy=RoundRobinStrategy())
    pool.add_server("a")
    pool.add_server("b")
    pool.add_server("c")

    pool.mark_unhealthy("b")

    seen: set[str] = set()
    for _ in range(50):
        server = pool.get_server(req_id=0)
        assert server is not None
        assert server != "b"
        seen.add(server)

    assert seen == {"a", "c"}


def test_all_servers_returns_regardless_of_health() -> None:
    pool = ServerPool(strategy=RoundRobinStrategy())
    pool.add_server("a")
    pool.add_server("b")
    pool.mark_unhealthy("b")

    assert "a" in pool.all_servers
    assert "b" in pool.all_servers


def test_remove_server_cleans_up() -> None:
    pool = ServerPool(strategy=RoundRobinStrategy())
    pool.add_server("a")
    pool.add_server("b")
    pool.remove_server("a")

    assert "a" not in pool.all_servers
    assert "b" in pool.all_servers


def test_mark_healthy_restores_server() -> None:
    pool = ServerPool(strategy=RoundRobinStrategy())
    pool.add_server("a")
    pool.add_server("b")

    pool.mark_unhealthy("a")
    pool.mark_healthy("a")

    seen: set[str] = set()
    for _ in range(20):
        server = pool.get_server(req_id=0)
        assert server is not None
        seen.add(server)

    assert "a" in seen
    assert "b" in seen
