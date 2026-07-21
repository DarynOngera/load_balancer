from __future__ import annotations

import asyncio
import json
import random

from aiohttp import web

from load_balancer.config import settings
from load_balancer.docker.manager import DockerManager, random_hostname
from load_balancer.health.state import ServerPool
from load_balancer.network.proxy import ProxyClient


def create_app(
    pool: ServerPool, proxy: ProxyClient, docker_mgr: DockerManager
) -> web.Application:
    app = web.Application()

    async def get_replicas(request: web.Request) -> web.Response:
        servers = pool.active_servers()
        return web.json_response(
            {"N": len(servers), "replicas": servers, "status": "successful"}
        )

    async def add_servers(request: web.Request) -> web.Response:
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"message": "Invalid JSON", "status": "failure"}, status=400
            )
        n = payload.get("n", 0)
        hostnames = payload.get("hostnames", [])

        if not isinstance(n, int):
            return web.json_response(
                {"message": "'n' must be an integer", "status": "failure"}, status=400
            )
        if not isinstance(hostnames, list):
            return web.json_response(
                {"message": "'hostnames' must be a list", "status": "failure"},
                status=400,
            )

        if len(hostnames) > n:
            return web.json_response(
                {
                    "message": "Length of hostname list exceeds new instance count",
                    "status": "failure",
                },
                status=400,
            )

        for hostname in hostnames:
            if not isinstance(hostname, str) or not hostname:
                return web.json_response(
                    {"message": f"Invalid hostname: {hostname}", "status": "failure"},
                    status=400,
                )
            await asyncio.to_thread(docker_mgr.spawn, hostname)

        for _ in range(n - len(hostnames)):
            await asyncio.to_thread(docker_mgr.spawn, random_hostname())

        servers = pool.active_servers()
        return web.json_response(
            {"N": len(servers), "replicas": servers, "status": "successful"}
        )

    async def remove_servers(request: web.Request) -> web.Response:
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"message": "Invalid JSON", "status": "failure"}, status=400
            )
        n = payload.get("n", 0)
        hostnames = payload.get("hostnames", [])

        if not isinstance(n, int):
            return web.json_response(
                {"message": "'n' must be an integer", "status": "failure"}, status=400
            )
        if not isinstance(hostnames, list):
            return web.json_response(
                {"message": "'hostnames' must be a list", "status": "failure"},
                status=400,
            )

        current = pool.active_servers()

        if len(hostnames) > n:
            return web.json_response(
                {
                    "message": "Length of hostname list exceeds removable instances",
                    "status": "failure",
                },
                status=400,
            )

        for hostname in hostnames:
            if hostname in current:
                await asyncio.to_thread(docker_mgr.remove, hostname)
                current.remove(hostname)

        remaining = n - len(hostnames)
        if remaining > 0 and current:
            selected = random.sample(current, min(remaining, len(current)))
            for hostname in selected:
                await asyncio.to_thread(docker_mgr.remove, hostname)

        servers = pool.active_servers()
        return web.json_response(
            {"N": len(servers), "replicas": servers, "status": "successful"}
        )

    async def handle_route(request: web.Request) -> web.Response:
        req_id = random.randint(100000, 999999)
        method = request.method
        path = request.match_info.get("path", "")
        if request.query_string:
            path = f"{path}?{request.query_string}"
        headers = dict(request.headers)
        body = await request.read()
        client_ip = request.remote or ""

        resp_headers, resp_body, status = await proxy.forward(
            method, path, req_id, headers=headers, body=body, client_ip=client_ip
        )
        return web.Response(body=resp_body, status=status, headers=resp_headers)

    app.router.add_get("/rep", get_replicas)
    app.router.add_post("/add", add_servers)
    app.router.add_delete("/rm", remove_servers)
    app.router.add_route("*", "/{path:.*}", handle_route)

    return app


async def run_server(
    pool: ServerPool, proxy: ProxyClient, docker_mgr: DockerManager
) -> None:
    app = create_app(pool, proxy, docker_mgr)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.lb_host, settings.lb_port)
    await site.start()
    print(f"Load balancer listening on {settings.lb_host}:{settings.lb_port}")
