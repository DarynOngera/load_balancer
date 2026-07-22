from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import aiohttp

from load_balancer.config import settings
from load_balancer.health.state import ServerPool
from load_balancer.network.metrics import (
    BACKENDS_ACTIVE,
    BACKENDS_HEALTHY,
    REQUEST_COUNT,
    REQUEST_DURATION,
    RETRIES_TOTAL,
)

logger = logging.getLogger(__name__)


def _backoff_delay(attempt: int) -> float:
    return min(
        settings.retry_base_delay * (2**attempt),
        settings.retry_max_delay,
    )


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
        request_id: str = "",
    ) -> tuple[dict[str, str], bytes, int]:
        start = time.monotonic()
        excluded: list[str] = []

        BACKENDS_ACTIVE.set(len(self._pool.active_servers()))
        BACKENDS_HEALTHY.set(len(self._pool.healthy_servers()))

        for attempt in range(settings.max_retries + 1):
            server = self._pool.get_server(
                req_id=req_id, client_ip=client_ip, exclude=excluded or None
            )
            if server is None:
                break

            assert self._session is not None
            target_url = f"http://{server}:{settings.backend_port}/{path}"
            try:
                async with self._session.request(
                    method, target_url, headers=headers, data=body
                ) as resp:
                    resp_body = await resp.read()
                    REQUEST_COUNT.labels(method=method, status=str(resp.status)).inc()
                    REQUEST_DURATION.labels(method=method).observe(
                        time.monotonic() - start
                    )
                    logger.debug(
                        "Fwd [%s] %s %s → %s %s",
                        request_id,
                        method,
                        path,
                        server,
                        resp.status,
                    )
                    return dict(resp.headers), resp_body, resp.status
            except (asyncio.TimeoutError, aiohttp.ClientError):
                self._pool.mark_unhealthy(server)
                excluded.append(server)
                RETRIES_TOTAL.inc()
                logger.warning(
                    "Fwd [%s] %s %s → %s failed (attempt %d)",
                    request_id,
                    method,
                    path,
                    server,
                    attempt,
                )
                if attempt < settings.max_retries:
                    await asyncio.sleep(_backoff_delay(attempt))

        if not excluded:
            logger.warning("Fwd [%s] no healthy servers", request_id)
            return {}, b'{"message": "No servers available", "status": "failure"}', 503
        logger.error(
            "Fwd [%s] all backends failed after %d retries",
            request_id,
            settings.max_retries,
        )
        return {}, b'{"message": "Backend request failed", "status": "failure"}', 502
