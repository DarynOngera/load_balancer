from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LoadBalancingStrategy(ABC):
    @abstractmethod
    def select_server(
        self,
        servers: list[str],
        context: Optional[Dict[str, Any]] = None,
        exclude: Optional[list[str]] = None,
    ) -> Optional[str]: ...

    @abstractmethod
    def add_server(self, server: str) -> None: ...

    @abstractmethod
    def remove_server(self, server: str) -> None: ...
