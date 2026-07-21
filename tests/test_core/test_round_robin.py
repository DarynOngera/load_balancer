from __future__ import annotations

from load_balancer.core.round_robin import RoundRobinStrategy


def test_round_robin_cycles() -> None:
    strategy = RoundRobinStrategy()
    strategy.add_server("a")
    strategy.add_server("b")
    strategy.add_server("c")

    assert strategy.select_server([]) == "a"
    assert strategy.select_server([]) == "b"
    assert strategy.select_server([]) == "c"
    assert strategy.select_server([]) == "a"


def test_remove_current_index() -> None:
    strategy = RoundRobinStrategy()
    strategy.add_server("a")
    strategy.add_server("b")
    strategy.add_server("c")

    strategy.select_server([])
    strategy.select_server([])
    strategy.remove_server("b")

    assert strategy.select_server([]) == "c"
    assert strategy.select_server([]) == "a"


def test_empty_returns_none() -> None:
    strategy = RoundRobinStrategy()
    assert strategy.select_server([]) is None
