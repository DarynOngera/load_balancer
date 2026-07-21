from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from load_balancer.config import Settings
from load_balancer.network.proxy import _backoff_delay


class _MockResponse:
    def __init__(self, status: int = 200, body: bytes = b"ok", headers: dict | None = None) -> None:
        self.status = status
        self._body = body
        self._headers = headers or {}

    async def __aenter__(self) -> _MockResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def read(self) -> bytes:
        return self._body

    @property
    def headers(self) -> dict:
        return self._headers


class TestBackoffDelay:
    def _make_settings(self, base: float, max_delay: float) -> MagicMock:
        s = MagicMock(spec=Settings)
        s.retry_base_delay = base
        s.retry_max_delay = max_delay
        return s

    def test_backoff_delay_zero(self) -> None:
        with patch("load_balancer.network.proxy.settings", self._make_settings(0.1, 2.0)):
            assert _backoff_delay(0) == 0.1

    def test_backoff_delay_exponential(self) -> None:
        with patch("load_balancer.network.proxy.settings", self._make_settings(0.1, 2.0)):
            assert _backoff_delay(1) == 0.2
            assert _backoff_delay(2) == 0.4
            assert _backoff_delay(3) == 0.8
            assert _backoff_delay(4) == 1.6

    def test_backoff_delay_capped(self) -> None:
        with patch("load_balancer.network.proxy.settings", self._make_settings(1.0, 3.0)):
            assert _backoff_delay(0) == 1.0
            assert _backoff_delay(1) == 2.0
            assert _backoff_delay(2) == 3.0
            assert _backoff_delay(10) == 3.0


@pytest.mark.asyncio
async def test_forward_retries_on_transport_error() -> None:
    mock_pool = MagicMock()
    mock_pool.get_server = MagicMock(side_effect=[
        "server-a",
        "server-b",
    ])
    mock_session = MagicMock()
    mock_session.request = MagicMock(side_effect=[
        aiohttp.ClientError("connection refused"),
        _MockResponse(),
    ])

    mock_settings = MagicMock(spec=Settings)
    mock_settings.max_retries = 2
    mock_settings.retry_base_delay = 0.1
    mock_settings.retry_max_delay = 2.0
    mock_settings.backend_port = 5000
    mock_settings.request_timeout = 5

    with (
        patch("load_balancer.network.proxy.settings", mock_settings),
        patch("load_balancer.network.proxy.asyncio.sleep", AsyncMock()) as mock_sleep,
    ):
        from load_balancer.network.proxy import ProxyClient
        proxy = ProxyClient(pool=mock_pool)
        proxy._session = mock_session

        headers, body, status = await proxy.forward("GET", "test", 1)

        assert status == 200
        assert body == b"ok"
        assert mock_pool.get_server.call_count == 2
        mock_pool.mark_unhealthy.assert_called_once_with("server-a")
        mock_sleep.assert_awaited_once()


@pytest.mark.asyncio
async def test_forward_all_retries_exhausted() -> None:
    mock_pool = MagicMock()
    mock_pool.get_server = MagicMock(side_effect=[
        "server-a",
        "server-b",
        None,
    ])
    mock_session = MagicMock()
    mock_session.request = MagicMock(side_effect=[
        aiohttp.ClientError("connection refused"),
        aiohttp.ClientError("connection refused"),
    ])

    mock_settings = MagicMock(spec=Settings)
    mock_settings.max_retries = 2
    mock_settings.retry_base_delay = 0.1
    mock_settings.retry_max_delay = 2.0
    mock_settings.backend_port = 5000
    mock_settings.request_timeout = 5

    with (
        patch("load_balancer.network.proxy.settings", mock_settings),
        patch("load_balancer.network.proxy.asyncio.sleep", AsyncMock()),
    ):
        from load_balancer.network.proxy import ProxyClient
        proxy = ProxyClient(pool=mock_pool)
        proxy._session = mock_session

        headers, body, status = await proxy.forward("GET", "test", 1)

        assert status == 502
        assert mock_pool.get_server.call_count == 3
        assert mock_pool.mark_unhealthy.call_count == 2


@pytest.mark.asyncio
async def test_forward_no_servers_returns_503() -> None:
    mock_pool = MagicMock()
    mock_pool.get_server = MagicMock(return_value=None)
    mock_session = MagicMock()

    mock_settings = MagicMock(spec=Settings)
    mock_settings.max_retries = 2
    mock_settings.backend_port = 5000
    mock_settings.request_timeout = 5

    with patch("load_balancer.network.proxy.settings", mock_settings):
        from load_balancer.network.proxy import ProxyClient
        proxy = ProxyClient(pool=mock_pool)
        proxy._session = mock_session

        headers, body, status = await proxy.forward("GET", "test", 1)

        assert status == 503
