from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from load_balancer.core.interface import LoadBalancingStrategy


def _sha1_int(value: str) -> int:
    return int(hashlib.sha1(value.encode()).hexdigest(), 16)


class ConsistentHashStrategy(LoadBalancingStrategy):
    def __init__(
        self,
        total_slots: int = 512,
        num_virtual_servers: int = 9,
    ) -> None:
        self.total_slots = total_slots
        self.num_virtual_servers = num_virtual_servers
        self._hash_map: List[Optional[str]] = [None] * total_slots
        self._servers: Dict[str, List[int]] = {}

    def _request_hash(self, req_id: int) -> int:
        return (req_id + 2 * req_id**2 + 17) % self.total_slots

    def _virtual_server_hash(self, server_id: int, virtual_id: int) -> int:
        return (server_id + virtual_id + 2 * virtual_id**2 + 25) % self.total_slots

    def select_server(
        self, servers: list[str], context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not self._servers:
            return None
        req_id = (context or {}).get("req_id", 0)
        slot = self._request_hash(req_id)
        while self._hash_map[slot] is None:
            slot = (slot + 1) % self.total_slots
        return self._hash_map[slot]

    def add_server(self, server: str) -> None:
        if server in self._servers:
            self.remove_server(server)
        server_id = _sha1_int(server)
        self._servers[server] = []
        for j in range(self.num_virtual_servers):
            slot = self._virtual_server_hash(server_id, j)
            while self._hash_map[slot] is not None:
                slot = (slot + 1) % self.total_slots
            self._hash_map[slot] = server
            self._servers[server].append(slot)

    def remove_server(self, server: str) -> None:
        slots = self._servers.pop(server, None)
        if slots is None:
            return
        for slot in slots:
            self._hash_map[slot] = None

    @property
    def servers(self) -> Dict[str, List[int]]:
        return dict(self._servers)
