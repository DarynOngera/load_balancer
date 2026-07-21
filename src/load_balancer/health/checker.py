from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp

from load_balancer.config import settings
from load_balancer.health.state import ServerPool


class HealthChecker:
    def __init__(self, pool: ServerPool) -> None:
        self._pool = pool
        self._session: Optional[aiohttp.ClientSession] = None
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

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
        servers = self._pool.all_servers
        for server in servers:
            if not self._running:
                break
            try:
                url = f"http://{server}:{settings.backend_port}/heartbeat"
                async with self._session.get(url, timeout=settings.request_timeout):
                    self._pool.mark_healthy(server)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                self._pool.mark_unhealthy(server)
