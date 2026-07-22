from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    server_image: str = "server-img"
    network_name: str = "net1"
    initial_replica_count: int = 3
    total_slots: int = 10000
    num_virtual_servers: int = 100
    request_timeout: int = 5
    health_check_interval: int = 10
    lb_host: str = "0.0.0.0"
    lb_port: int = 5000
    backend_port: int = 5000
    hashing_mode: str = "sticky"
    log_level: str = "INFO"
    max_retries: int = 2
    retry_base_delay: float = 0.1
    retry_max_delay: float = 2.0


settings = Settings()
