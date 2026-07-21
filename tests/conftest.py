from __future__ import annotations

from typing import Any, Dict

from pytest import fixture

from load_balancer.core.consistent_hash import ConsistentHashStrategy


@fixture
def consistent_hash() -> ConsistentHashStrategy:
    return ConsistentHashStrategy(total_slots=512, num_virtual_servers=9)
