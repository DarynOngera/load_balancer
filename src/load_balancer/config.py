from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    server_image: str = "server-img"
    network_name: str = "net1"
    initial_replica_count: int = 3
    total_slots: int = 512
    num_virtual_servers: int = 9
    request_timeout: int = 5
    health_check_interval: int = 10
    lb_host: str = "0.0.0.0"
    lb_port: int = 5000
    backend_port: int = 5000


settings = Settings()
