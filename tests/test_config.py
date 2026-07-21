from __future__ import annotations

from load_balancer.config import Settings


def test_defaults() -> None:
    settings = Settings()
    assert settings.server_image == "server-img"
    assert settings.network_name == "net1"
    assert settings.initial_replica_count == 3
    assert settings.total_slots == 10000
    assert settings.num_virtual_servers == 100
    assert settings.hashing_mode == "sticky"
    assert settings.request_timeout == 5
    assert settings.health_check_interval == 10
    assert settings.lb_host == "0.0.0.0"
    assert settings.lb_port == 5000
    assert settings.backend_port == 5000
