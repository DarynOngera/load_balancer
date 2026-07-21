from __future__ import annotations

from typing import Any, Dict, Optional

from load_balancer.core.interface import LoadBalancingStrategy


class RoundRobinStrategy(LoadBalancingStrategy):
    def __init__(self) -> None:
        self._servers: list[str] = []
        self._index: int = 0

    def select_server(
        self,
        servers: list[str],
        context: Optional[Dict[str, Any]] = None,
        exclude: Optional[list[str]] = None,
    ) -> Optional[str]:
        excluded = set(exclude or [])
        available = [s for s in servers if s not in excluded]
        if not available:
            return None
        self._index = self._index % len(available)
        server = available[self._index]
        self._index = (self._index + 1) % len(available)
        return server

    def add_server(self, server: str) -> None:
        if server not in self._servers:
            self._servers.append(server)

    def remove_server(self, server: str) -> None:
        if server in self._servers:
            idx = self._servers.index(server)
            self._servers.remove(server)
            if idx < self._index:
                self._index -= 1
            if self._index >= len(self._servers) and self._servers:
                self._index = 0
