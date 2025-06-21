from flask import Flask, jsonify, request
import os
import docker
import random
import string
import requests
import time

app = Flask(__name__)

# --- Consistent Hashing Implementation (from before) ---
class ConsistentHashMap:
    def __init__(self, total_slots=512, num_virtual_servers=9):
        self.total_slots = total_slots
        self.num_virtual_servers = num_virtual_servers
        self.hash_map = [None] * self.total_slots
        self.servers = {}

    def get_request_hash(self, req_id):
        return (req_id + 2 * req_id**2 + 17) % self.total_slots

    def get_virtual_server_hash(self, server_id, virtual_server_id):
        return (server_id + virtual_server_id + 2 * virtual_server_id**2 + 25) % self.total_slots

    def add_server(self, server_name):
        server_id = hash(server_name)
        self.servers[server_name] = []
        for j in range(self.num_virtual_servers):
            slot = self.get_virtual_server_hash(server_id, j)
            while self.hash_map[slot] is not None:
                slot = (slot + 1) % self.total_slots
            self.hash_map[slot] = server_name
            self.servers[server_name].append(slot)

    def remove_server(self, server_name):
        if server_name not in self.servers:
            return
        for slot in self.servers[server_name]:
            self.hash_map[slot] = None
        del self.servers[server_name]

    def get_server_for_request(self, req_id):
        if not self.servers:
            return None
        slot = self.get_request_hash(req_id)
        while self.hash_map[slot] is None:
            slot = (slot + 1) % self.total_slots
        return self.hash_map[slot]

# --- Docker and Load Balancer Management ---
consistent_hash_map = ConsistentHashMap()
docker_client = docker.from_env()
SERVER_IMAGE = "server-img" # Image name from docker-compose.yml
NETWORK_NAME = "net1"       # Network name from docker-compose.yml

def get_random_hostname(length=6):
    return "server_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def spawn_server(hostname):
    """Spawns a new server container with a given hostname."""
    try:
        container = docker_client.containers.run(
            SERVER_IMAGE,
            name=hostname,
            hostname=hostname,
            network=NETWORK_NAME,
            environment={"SERVER_ID": hostname},
            detach=True
        )
        consistent_hash_map.add_server(hostname)
        print(f"Successfully spawned and added server: {hostname}")
        return container
    except docker.errors.APIError as e:
        print(f"Error spawning server {hostname}: {e}")
        return None

def remove_server_container(hostname):
    """Stops and removes a server container."""
    try:
        container = docker_client.containers.get(hostname)
        container.stop()
        container.remove()
        consistent_hash_map.remove_server(hostname)
        print(f"Successfully removed server: {hostname}")
    except docker.errors.NotFound:
        print(f"Server {hostname} not found, removing from map anyway.")
        consistent_hash_map.remove_server(hostname)
    except docker.errors.APIError as e:
        print(f"Error removing server {hostname}: {e}")

# --- API Endpoints ---
@app.route('/rep', methods=['GET'])
def get_replicas():
    replicas = list(consistent_hash_map.servers.keys())
    return jsonify({
        "N": len(replicas),
        "replicas": replicas,
        "status": "successful"
    }), 200

@app.route('/add', methods=['POST'])
def add_servers():
    payload = request.get_json()
    n = payload.get('n')
    hostnames = payload.get('hostnames', [])

    if len(hostnames) > n:
        return jsonify({"message": "<Error> Length of hostname list is more than newly added instances", "status": "failure"}), 400

    # Add specified hostnames
    for hostname in hostnames:
        spawn_server(hostname)
    
    # Add random hostnames for the remaining count
    for _ in range(n - len(hostnames)):
        hostname = get_random_hostname()
        spawn_server(hostname)

    return get_replicas()

@app.route('/rm', methods=['DELETE'])
def remove_servers():
    payload = request.get_json()
    n = payload.get('n')
    hostnames_to_remove = payload.get('hostnames', [])

    if len(hostnames_to_remove) > n:
        return jsonify({"message": "<Error> Length of hostname list is more than removable instances", "status": "failure"}), 400

    current_replicas = list(consistent_hash_map.servers.keys())
    
    # Remove specified hostnames
    for hostname in hostnames_to_remove:
        if hostname in current_replicas:
            remove_server_container(hostname)
            current_replicas.remove(hostname)
    
    # Remove random hostnames for the remaining count
    num_to_remove_randomly = n - len(hostnames_to_remove)
    if num_to_remove_randomly > 0 and current_replicas:
        random_servers_to_remove = random.sample(current_replicas, min(num_to_remove_randomly, len(current_replicas)))
        for hostname in random_servers_to_remove:
            remove_server_container(hostname)

    return get_replicas()

@app.route('/<path:path>', methods=['GET'])
def route_request(path):
    req_id = random.randint(100000, 999999)
    server_name = consistent_hash_map.get_server_for_request(req_id)

    if not server_name:
        return jsonify({"message": "<Error> No servers available to handle the request", "status": "failure"}), 503

    try:
        # Forward the request to the chosen server
        # The URL is based on the container's hostname within the Docker network
        target_url = f'http://{server_name}:5000/{path}'
        resp = requests.get(target_url)
        return resp.json(), resp.status_code
    except requests.exceptions.RequestException as e:
        print(f"Could not connect to {server_name}. Error: {e}")
        return jsonify({"message": f"<Error> '/{path}' endpoint does not exist or server is down.", "status": "failure"}), 400


def initialize_servers():
    """Cleans up old server containers and initializes N=3 new ones."""
    print("Initializing servers...")
    # Clean up any existing server containers from previous runs
    for container in docker_client.containers.list(filters={"ancestor": SERVER_IMAGE}):
        print(f"Removing old container: {container.name}")
        container.stop()
        container.remove()

    # Spawn N initial servers as per assignment spec 
    for i in range(3):
        hostname = f"server{i}"
        spawn_server(hostname)

if __name__ == '__main__':
    initialize_servers()
    app.run(host='0.0.0.0', port=5000)
