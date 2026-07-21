from __future__ import annotations

from load_balancer.core.round_robin import RoundRobinStrategy


def test_round_robin_cycles() -> None:
    strategy = RoundRobinStrategy()
    servers = ["a", "b", "c"]

    assert strategy.select_server(servers) == "a"
    assert strategy.select_server(servers) == "b"
    assert strategy.select_server(servers) == "c"
    assert strategy.select_server(servers) == "a"


def test_remove_current_index() -> None:
    strategy = RoundRobinStrategy()
    strategy.add_server("a")
    strategy.add_server("b")
    strategy.add_server("c")

    strategy.select_server(["a", "b", "c"])
    strategy.select_server(["a", "b", "c"])
    strategy.remove_server("b")

    assert strategy.select_server(["a", "c"]) == "c"
    assert strategy.select_server(["a", "c"]) == "a"


def test_empty_returns_none() -> None:
    strategy = RoundRobinStrategy()
    assert strategy.select_server([]) is None


def test_exclude_skips_excluded_server() -> None:
    strategy = RoundRobinStrategy()
    for s in ["a", "b", "c"]:
        strategy.add_server(s)
    result = strategy.select_server(["a", "b", "c"], exclude=["a", "c"])
    assert result == "b"


def test_exclude_all_returns_none() -> None:
    strategy = RoundRobinStrategy()
    strategy.add_server("a")
    result = strategy.select_server(["a"], exclude=["a"])
    assert result is None


def test_filters_dead_servers() -> None:
    strategy = RoundRobinStrategy()
    strategy.add_server("a")
    strategy.add_server("b")
    strategy.add_server("c")

    healthy = ["a", "c"]
    assert strategy.select_server(healthy) == "a"
    assert strategy.select_server(healthy) == "c"
    assert strategy.select_server(healthy) == "a"
