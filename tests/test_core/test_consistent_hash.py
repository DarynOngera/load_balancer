from __future__ import annotations

from load_balancer.core.consistent_hash import ConsistentHashStrategy


def test_add_and_select_server(consistent_hash: ConsistentHashStrategy) -> None:
    consistent_hash.add_server("server0")
    consistent_hash.add_server("server1")
    consistent_hash.add_server("server2")

    servers = consistent_hash.servers
    assert "server0" in servers
    assert "server1" in servers
    assert "server2" in servers


def test_remove_server(consistent_hash: ConsistentHashStrategy) -> None:
    consistent_hash.add_server("server0")
    consistent_hash.remove_server("server0")
    assert "server0" not in consistent_hash.servers


def test_remove_nonexistent_server(consistent_hash: ConsistentHashStrategy) -> None:
    consistent_hash.remove_server("nonexistent")


def test_select_empty_ring(consistent_hash: ConsistentHashStrategy) -> None:
    result = consistent_hash.select_server(servers=[], context={"req_id": 12345})
    assert result is None


def test_deterministic_hashing() -> None:
    s1 = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9)
    s2 = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9)

    s1.add_server("server1")
    s2.add_server("server1")

    assert s1.servers == s2.servers


def test_server_occupied_slots(consistent_hash: ConsistentHashStrategy) -> None:
    consistent_hash.add_server("serverA")
    slots = consistent_hash.servers["serverA"]
    assert len(slots) == 9
    assert all(0 <= s < 512 for s in slots)


def test_select_respects_healthy_filter(consistent_hash: ConsistentHashStrategy) -> None:
    consistent_hash.add_server("server0")
    consistent_hash.add_server("server1")
    consistent_hash.add_server("server2")

    healthy = ["server0", "server2"]
    seen: set[str] = set()
    for req_id in range(100):
        server = consistent_hash.select_server(healthy, context={"req_id": req_id})
        assert server is not None
        assert server in healthy
        seen.add(server)

    assert "server1" not in seen


def test_select_returns_none_when_no_healthy(consistent_hash: ConsistentHashStrategy) -> None:
    consistent_hash.add_server("server0")
    consistent_hash.add_server("server1")

    result = consistent_hash.select_server([], context={"req_id": 42})
    assert result is None


def test_sticky_session_same_ip_returns_same_server() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="sticky")
    for s in ["server0", "server1", "server2"]:
        strategy.add_server(s)

    servers = list(strategy.servers.keys())
    results = []
    for _ in range(5):
        server = strategy.select_server(servers, context={"client_ip": "192.168.1.1"})
        results.append(server)

    assert all(r == results[0] for r in results)


def test_sticky_session_different_ips_can_differ() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="sticky")
    for s in ["server0", "server1", "server2"]:
        strategy.add_server(s)

    servers = list(strategy.servers.keys())
    server_a = strategy.select_server(servers, context={"client_ip": "10.0.0.1"})
    server_b = strategy.select_server(servers, context={"client_ip": "10.0.0.2"})
    assert server_a is not None
    assert server_b is not None
    assert isinstance(server_a, str)
    assert isinstance(server_b, str)


def test_sticky_filters_unhealthy() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="sticky")
    for s in ["server0", "server1", "server2"]:
        strategy.add_server(s)

    healthy = ["server0", "server2"]
    seen: set[str] = set()
    for octet in range(100):
        ip = f"192.168.0.{octet}"
        server = strategy.select_server(healthy, context={"client_ip": ip})
        assert server is not None
        assert server in healthy
        seen.add(server)

    assert "server1" not in seen


def test_sticky_fallback_to_req_id() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="sticky")
    strategy.add_server("server0")
    result = strategy.select_server(["server0"], context={"req_id": 42})
    assert result == "server0"


def test_exclude_skips_excluded_server() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="random")
    for s in ["server0", "server1"]:
        strategy.add_server(s)

    servers = list(strategy.servers.keys())
    for req_id in range(100):
        server = strategy.select_server(servers, context={"req_id": req_id}, exclude=["server0"])
        assert server == "server1"


def test_exclude_all_returns_none() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="random")
    strategy.add_server("server0")
    result = strategy.select_server(["server0"], context={"req_id": 42}, exclude=["server0"])
    assert result is None


def test_exclude_nonexistent_ignored() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="random")
    strategy.add_server("server0")
    result = strategy.select_server(["server0"], context={"req_id": 42}, exclude=["ghost"])
    assert result == "server0"


def test_random_mode_uses_req_id() -> None:
    strategy = ConsistentHashStrategy(total_slots=512, num_virtual_servers=9, hashing_mode="random")
    for s in ["server0", "server1", "server2"]:
        strategy.add_server(s)

    servers = list(strategy.servers.keys())
    results = []
    for _ in range(5):
        server = strategy.select_server(servers, context={"req_id": 12345})
        results.append(server)
    assert all(r == results[0] for r in results)
