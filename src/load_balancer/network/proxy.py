from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp

from load_balancer.config import settings
from load_balancer.health.state import ServerPool


class ProxyClient:
    def __init__(self, pool: ServerPool) -> None:
        self._pool = pool
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def stop(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def forward(
        self,
        method: str,
        path: str,
        req_id: int,
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        client_ip: str = "",
    ) -> tuple[dict[str, str], bytes, int]:
        server = self._pool.get_server(req_id=req_id, client_ip=client_ip)
        if server is None:
            return {}, b'{"message": "No servers available", "status": "failure"}', 503

        target_url = f"http://{server}:{settings.backend_port}/{path}"
        try:
            async with self._session.request(
                method, target_url, headers=headers, data=body
            ) as resp:
                resp_body = await resp.read()
                return dict(resp.headers), resp_body, resp.status
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            self._pool.mark_unhealthy(server)
            error_body = (
                b'{"message": "Backend request failed", "status": "failure"}'
            )
            return {}, error_body, 502
