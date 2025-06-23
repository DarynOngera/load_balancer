<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-blue.svg" alt="Language">
  <img src="https://img.shields.io/badge/Platform-Docker-blue.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

# Customizable Load Balancer in Docker

This project is an implementation of a customizable, fault-tolerant load balancer within a Docker environment. The system is designed to distribute asynchronous client requests evenly among a dynamic pool of web server replicas. The core of the load balancer uses a consistent hashing algorithm to efficiently map requests to servers, ensuring high availability and resource utilization.

---

## Table of Contents
1.  [Features](#features)
2.  [System Diagram](#system-diagram)
3.  [Prerequisites](#prerequisites)
4.  [Getting Started](#getting-started)
5.  [API Endpoints](#api-endpoints)
6.  [Design Choices and Assumptions](#design-choices-and-assumptions)
7.  [Testing and Performance Analysis](#testing-and-performance-analysis)

---

## Features

-   **Dynamic Scaling**: Add or remove server instances via API endpoints to scale with client demand.
-   **Fault Tolerance**: Automatically detects server failures and spawns new replicas to maintain the desired number of instances (`N`).
-   **Consistent Hashing**: Utilizes a custom-built consistent hash map with virtual servers to ensure even load distribution and minimal disruption when servers are added or removed.
-   **Dockerized Environment**: The entire system (load balancer and servers) is containerized and runs within an isolated Docker network (`net1`).

## Prerequisites

-   **OS**: Parrot OS{any os of your choosing }
-   **Docker**: Version 20.10.23 or above
-   **Docker Compose**: Standalone version v2.15.1 or above

## Getting Started

### Installation

1.  Clone the repository to your local machine:
    ```bash
    git clone <your-repo-link>
    cd <repo-name>
    ```

### Running the System

The included `Makefile` simplifies the process of building and running the application stack.

1.  **Build the Docker images** for the load balancer and the server:
    ```bash
    make build
    ```

2.  **Start the system**: This command will start the load balancer and initialize it with `N=3` server instances.
    ```bash
    make up
    ```

3.  **Shut down the system**: This command will stop and remove all running containers.
    ```bash
    make down
    ```

---

## API Endpoints

The load balancer exposes the following endpoints on `http://localhost:5000`.

### **`GET /rep`**
Returns the hostnames of all currently active server replicas.

| Method | Description                               | Example Command                      |
| :----- | :---------------------------------------- | :----------------------------------- |
| `GET`  | Fetches the list of active server replicas. | `curl http://localhost:5000/rep`     |

### **`POST /add`**
Adds a specified number of new server instances to scale up the system.

| Method | Description                                    | Payload                                                                                             | Example Command                                                                                                |
| :----- | :--------------------------------------------- | :-------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| `POST` | Adds `n` new server instances to the system.   | `{ "n": <integer>, "hostnames": [<string>, ...] }` <br/> *(`hostnames` list is optional)* | `curl -X POST -H "Content-Type: application/json" -d '{"n": 2, "hostnames": ["s10"]}' http://localhost:5000/add` |

### **`DELETE /rm`**
Removes a specified number of server instances to scale down the system.

| Method   | Description                                                                              | Payload                                                                                              | Example Command                                                                                                  |
| :------- | :--------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------- |
| `DELETE` | Removes `n` server instances. Can target specific hostnames or choose randomly if not specified. | `{ "n": <integer>, "hostnames": [<string>, ...] }` <br/> *(`hostnames` list is optional)* | `curl -X DELETE -H "Content-Type: application/json" -d '{"n": 1, "hostnames": ["s10"]}' http://localhost:5000/rm` |

### **`GET /<path>`**
Forwards the request to the appropriate server replica as determined by the consistent hashing algorithm.

| Method | Description                                                                   | Example Command                      |
| :----- | :---------------------------------------------------------------------------- | :----------------------------------- |
| `GET`  | Routes request to a valid endpoint on a server (e.g., `/home`).               | `curl http://localhost:5000/home`    |

---

## Design Choices and Assumptions

### Design Choices

-   **Application Framework**: Python with Flask was chosen for both the server and load balancer due to its lightweight nature and ease of development for creating simple HTTP endpoints.
-   **Docker Management**: The load balancer uses the `docker-py` Python library to interact directly with the host's Docker daemon. This allows it to dynamically spawn and remove server containers from within its own code.
-   **Consistent Hashing**: The consistent hash map was implemented as a Python class using a standard list to represent the 512-slot ring. Collisions during server placement are handled using linear probing as suggested.
-   **Asynchronous Testing**: The `tester.py` script uses `asyncio` and `aiohttp` to efficiently generate a high volume of concurrent requests, which is necessary for accurately simulating heavy load and testing the balancer's performance.

### Assumptions

-   **Environment**: The system assumes it is running on a Linux-based host with Docker and Docker Compose installed and properly configured.
-   **Networking**: It is assumed that all containers can communicate freely on the user-defined bridge network `net1` using their hostnames.
-   **Request IDs**: For simplicity, client requests are assigned a random 6-digit integer for mapping to the hash ring, as suggested in the assignment appendix.

---

## Testing and Performance Analysis

This section details the experiments performed to analyze the load balancer's performance, as required by **Task 4**.

### How to Run the Analysis

The `tester.py` script is used to generate load and collect data for the analysis. Before running, ensure the required Python libraries are installed:
```bash
pip install aiohttp matplotlib numpy
```

To run the test with 10,000 requests:
```bash
python tester.py
```

### A-1: Load Distribution Analysis
This test measures how evenly the load balancer distributes requests among `N=3` servers.

*Add your generated `load_distribution_chart.png` here.*

**Observations**:
*Fill in your observations here... Describe how evenly the requests were distributed. Mention the request counts for each server and comment on whether the consistent hashing algorithm provided a balanced distribution as expected.*

### A-2: Scalability Analysis
This test measures the average server load as the number of servers (`N`) is increased from 2 to 6.

*Add your generated scalability chart here.*

**Observations**:
*Fill in your observations here... Describe how the average load per server changed as N increased. A successful implementation should show the average load decreasing as more servers are added, demonstrating the scalability of the system.*

### A-3: Fault Tolerance Test
This test confirms that the load balancer can recover from a server failure by spawning a new instance.

**Test Steps**:
1.  The system was started with `N=3` servers.
2.  A single server container (e.g., `server1`) was manually stopped using `docker stop server1`.
3.  The `/rep` endpoint was polled to observe the system's response.

**Observations**:
*Fill in your observations here... Describe how the list of replicas changed after the failure. Confirm that the load balancer detected the failure and quickly spawned a new, randomly-named container to bring the total number of active replicas back to 3.*

### Advanced Analysis: Latency & Performance
This analysis provides deeper insight into the performance characteristics of the load balancer. The `tester.py` script was updated to capture latency for each request and generate the following visualizations.

*Add your generated `full_analysis_report.png` here.*

**Observations**:
*Fill in your observations here... Comment on the latency histogram and box plot. Is the latency consistent? Are there many outliers? Discuss what these metrics imply about the performance of the system.*
