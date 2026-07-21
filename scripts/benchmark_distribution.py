from __future__ import annotations

import math
import random

from load_balancer.core.consistent_hash import ConsistentHashStrategy


def benchmark_virtual_servers(
    num_servers: int = 10,
    num_requests: int = 10000,
    virtual_counts: list[int] | None = None,
) -> None:
    if virtual_counts is None:
        virtual_counts = [9, 50, 100, 200]

    print(f"Servers: {num_servers}, Requests: {num_requests}")
    print(f"{'Virt':>6} | {'Mean':>8} | {'StdDev':>8} | {'Min':>6} | {'Max':>6} | {'Ratio':>6}")
    print("-" * 55)

    for v in virtual_counts:
        total_slots = max(512, v * num_servers * 3)
        strategy = ConsistentHashStrategy(total_slots=total_slots, num_virtual_servers=v)

        for i in range(num_servers):
            strategy.add_server(f"server-{i}")

        counts: dict[str, int] = {}
        for _ in range(num_requests):
            req_id = random.randint(0, 999999)
            server = strategy.select_server(
                list(strategy.servers.keys()),
                context={"req_id": req_id},
            )
            if server is not None:
                counts[server] = counts.get(server, 0) + 1

        values = list(counts.values())
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        stddev = math.sqrt(variance)
        ratio = stddev / mean * 100 if mean > 0 else 0

        print(
            f"{v:>6} | {mean:>8.1f} | {stddev:>8.2f} | {min(values):>6} | "
            f"{max(values):>6} | {ratio:>5.1f}%"
        )


if __name__ == "__main__":
    benchmark_virtual_servers()
