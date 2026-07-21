from __future__ import annotations

import random
import string
from typing import List, Optional

import docker
from docker.errors import APIError, NotFound

from load_balancer.config import settings
from load_balancer.health.state import ServerPool


def random_hostname(length: int = 6) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"server_{suffix}"


class DockerManager:
    def __init__(self, pool: ServerPool) -> None:
        self._pool = pool
        self._client = docker.from_env()

    def spawn(self, hostname: str) -> Optional[str]:
        try:
            self._client.containers.run(
                settings.server_image,
                name=hostname,
                hostname=hostname,
                network=settings.network_name,
                environment={"SERVER_ID": hostname},
                detach=True,
            )
            self._pool.add_server(hostname)
            print(f"Spawned server: {hostname}")
            return hostname
        except APIError as e:
            print(f"Failed to spawn {hostname}: {e}")
            return None

    def remove(self, hostname: str) -> None:
        try:
            container = self._client.containers.get(hostname)
            container.stop()
            container.remove()
            print(f"Removed server: {hostname}")
        except NotFound:
            print(f"Container {hostname} not found")
        except APIError as e:
            print(f"Failed to remove {hostname}: {e}")
        finally:
            self._pool.remove_server(hostname)

    def initialize(self, count: Optional[int] = None) -> List[str]:
        count = count or settings.initial_replica_count
        spawned: List[str] = []

        for container in self._client.containers.list(
            all=True, filters={"ancestor": settings.server_image}
        ):
            try:
                container.stop()
                container.remove()
            except APIError:
                pass

        for i in range(count):
            hostname = f"server{i}"
            result = self.spawn(hostname)
            if result:
                spawned.append(result)

        return spawned

    def scale(self, delta: int) -> None:
        if delta > 0:
            for _ in range(delta):
                self.spawn(random_hostname())
        elif delta < 0:
            current = self._pool.active_servers()
            to_remove = random.sample(
                current, min(abs(delta), len(current))
            )
            for hostname in to_remove:
                self.remove(hostname)
