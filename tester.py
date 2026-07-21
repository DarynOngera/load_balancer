import asyncio
import aiohttp
from collections import Counter
import time
import matplotlib.pyplot as plt

# Use a semaphore to limit the number of concurrent requests
SEMAPHORE = asyncio.Semaphore(100) 

async def fetch(session, url):
    """Sends a single GET request under the control of a semaphore."""
    async with SEMAPHORE:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    message = data.get("message", "")
                    if "Hello from Server:" in message:
                        server_id = message.split(":")[-1].strip()
                        return server_id
                else:
                    print(f"Received status {response.status}")
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

def plot_results(server_counts, num_requests):
    """Generates and saves a bar chart of the request distribution."""
    if not server_counts:
        print("\nNo data to plot as no requests were successful.")
        return

    servers = list(server_counts.keys())
    counts = list(server_counts.values())

    plt.figure(figsize=(10, 6))
    plt.bar(servers, counts, color='skyblue')
    
    plt.xlabel('Server Instances')
    plt.ylabel('Number of Requests Handled')
    plt.title(f'Load Distribution Among Servers for {num_requests} Requests')
    plt.xticks(rotation=45, ha="right") # Rotate labels for better readability if names are long
    plt.tight_layout() # Adjust layout to make room for rotated labels
    plt.grid(axis='y', linestyle='--')

    # Save the chart to a file
    chart_filename = 'load_distribution_chart.png'
    plt.savefig(chart_filename)
    print(f"\nChart saved as '{chart_filename}'")


async def run_test(url, num_requests):
    """Runs the load balancing test and plots the results."""
    tasks = []
    server_counts = Counter()
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        for _ in range(num_requests):
            tasks.append(fetch(session, url))
            
        responses = await asyncio.gather(*tasks)
        
        for server_id in responses:
            if server_id:
                server_counts[server_id] += 1

    end_time = time.time()
    
    print(f"Test completed in {end_time - start_time:.2f} seconds.")
    print("\nRequest distribution:")
    total_requests_handled = 0
    if not server_counts:
        print("  No successful requests were handled.")
    else:
        for server, count in sorted(server_counts.items()):
            print(f"  {server}: {count} requests")
            total_requests_handled += count
    
    print(f"\nTotal successful requests: {total_requests_handled}/{num_requests}")
    
    # Generate the bar chart from the results
    plot_results(server_counts, num_requests)

if __name__ == '__main__':
    LOAD_BALANCER_URL = "http://localhost:5000/home"
    NUM_REQUESTS = 1000000
    
    # Make sure you have matplotlib installed: pip install matplotlib
    print(f"Starting test with {NUM_REQUESTS} async requests to {LOAD_BALANCER_URL}...")
    asyncio.run(run_test(LOAD_BALANCER_URL, NUM_REQUESTS))
