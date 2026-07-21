from __future__ import annotations

from typing import Any, Dict, Optional

from load_balancer.core.interface import LoadBalancingStrategy


class RoundRobinStrategy(LoadBalancingStrategy):
    def __init__(self) -> None:
        self._servers: list[str] = []
        self._index: int = 0

    def select_server(
        self, servers: list[str], context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not self._servers:
            return None
        server = self._servers[self._index]
        self._index = (self._index + 1) % len(self._servers)
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
