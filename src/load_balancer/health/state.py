from __future__ import annotations

import asyncio
from enum import Enum, auto
from typing import Dict, List, Optional

from load_balancer.core.interface import LoadBalancingStrategy


class ServerStatus(Enum):
    HEALTHY = auto()
    UNHEALTHY = auto()
    DRAINING = auto()


class ServerPool:
    def __init__(self, strategy: LoadBalancingStrategy) -> None:
        self._strategy = strategy
        self._status: Dict[str, ServerStatus] = {}
        self._lock = asyncio.Lock()

    def active_servers(self) -> list[str]:
        return [
            s
            for s, st in self._status.items()
            if st in (ServerStatus.HEALTHY, ServerStatus.DRAINING)
        ]

    def healthy_servers(self) -> list[str]:
        return [s for s, st in self._status.items() if st == ServerStatus.HEALTHY]

    def get_server(self, req_id: int = 0) -> Optional[str]:
        return self._strategy.select_server(
            self.healthy_servers(), context={"req_id": req_id}
        )

    def add_server(self, server: str) -> None:
        self._strategy.add_server(server)
        self._status[server] = ServerStatus.HEALTHY

    def remove_server(self, server: str) -> None:
        self._strategy.remove_server(server)
        self._status.pop(server, None)

    def mark_unhealthy(self, server: str) -> None:
        if server in self._status:
            self._status[server] = ServerStatus.UNHEALTHY

    def mark_healthy(self, server: str) -> None:
        if server in self._status:
            self._status[server] = ServerStatus.HEALTHY

    @property
    def all_servers(self) -> List[str]:
        return list(self._status.keys())
