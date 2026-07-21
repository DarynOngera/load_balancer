from __future__ import annotations

import asyncio

from load_balancer.config import settings
from load_balancer.core.consistent_hash import ConsistentHashStrategy
from load_balancer.docker.manager import DockerManager
from load_balancer.health.checker import HealthChecker
from load_balancer.health.state import ServerPool
from load_balancer.network.proxy import ProxyClient
from load_balancer.network.server import run_server


async def _async_main() -> None:
    strategy = ConsistentHashStrategy(
        total_slots=settings.total_slots,
        num_virtual_servers=settings.num_virtual_servers,
        hashing_mode=settings.hashing_mode,
    )
    pool = ServerPool(strategy=strategy)
    docker_mgr = DockerManager(pool=pool)
    proxy = ProxyClient(pool=pool)
    health = HealthChecker(pool=pool)

    await asyncio.to_thread(docker_mgr.initialize)

    await proxy.start()
    await health.start()

    try:
        await run_server(pool, proxy, docker_mgr)
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await health.stop()
        await proxy.stop()


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
