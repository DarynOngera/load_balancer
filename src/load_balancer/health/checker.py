from __future__ import annotations

import asyncio
from typing import Dict, Optional

import aiohttp

from load_balancer.config import settings
from load_balancer.health.state import ServerPool, ServerStatus


class HealthChecker:
    def __init__(self, pool: ServerPool) -> None:
        self._pool = pool
        self._session: Optional[aiohttp.ClientSession] = None
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._failures: Dict[str, int] = {}
        self._last_checked: Dict[str, float] = {}

    async def start(self) -> None:
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def _loop(self) -> None:
        while self._running:
            await asyncio.sleep(settings.health_check_interval)
            if not self._running:
                break
            await self._check_all()

    async def _check_all(self) -> None:
        now = asyncio.get_event_loop().time()
        servers = self._pool.all_servers
        for server in servers:
            if not self._running:
                break
            if not self._should_check(server, now):
                continue
            self._last_checked[server] = now
            try:
                url = f"http://{server}:{settings.backend_port}/heartbeat"
                assert self._session is not None
                async with self._session.get(
                    url, timeout=aiohttp.ClientTimeout(total=settings.request_timeout)
                ):
                    self._pool.mark_healthy(server)
                    self._failures.pop(server, None)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                self._pool.mark_unhealthy(server)
                self._failures[server] = self._failures.get(server, 0) + 1

    def _should_check(self, server: str, now: float) -> bool:
        status = self._pool.get_status(server)
        if status != ServerStatus.UNHEALTHY:
            return True
        last = self._last_checked.get(server, 0.0)
        failures = self._failures.get(server, 0)
        backoff = min(
            settings.retry_base_delay * (2**failures), settings.retry_max_delay
        )
        return (now - last) >= backoff
