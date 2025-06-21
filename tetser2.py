import asyncio
import aiohttp
from collections import Counter
import time
import matplotlib.pyplot as plt
import numpy as np

# Use a semaphore to limit the number of concurrent requests
SEMAPHORE = asyncio.Semaphore(100) 

async def fetch(session, url):
    """
    Sends a single GET request and returns a tuple of (server_id, latency).
    """
    start_time = time.time()
    async with SEMAPHORE:
        try:
            async with session.get(url, timeout=10) as response:
                latency = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    message = data.get("message", "")
                    if "Hello from Server:" in message:
                        server_id = message.split(":")[-1].strip()
                        return (server_id, latency)
                # Return latency even if the request was not successful, but with no server_id
                return (None, latency)
        except Exception as e:
            latency = time.time() - start_time
            print(f"An error occurred: {e} after {latency:.2f}s")
            return (None, latency)

def generate_visualizations(server_counts, latencies, num_requests):
    """
    Generates and saves a figure with multiple plots:
    1. A bar chart of the request distribution.
    2. A histogram of request latencies.
    3. A box plot of request latencies.
    """
    if not server_counts:
        print("\nNo data to plot as no requests were successful.")
        return

    # Create a figure with 3 subplots
    fig, axs = plt.subplots(3, 1, figsize=(10, 18))

    # --- Plot 1: Load Distribution Bar Chart ---
    servers = list(server_counts.keys())
    counts = list(server_counts.values())
    axs[0].bar(servers, counts, color='skyblue')
    axs[0].set_title(f'Load Distribution for {num_requests} Requests')
    axs[0].set_xlabel('Server Instances')
    axs[0].set_ylabel('Number of Requests Handled')
    axs[0].grid(axis='y', linestyle='--')

    # --- Plot 2: Latency Distribution Histogram ---
    axs[1].hist(latencies, bins=50, color='c', edgecolor='black')
    axs[1].set_title('Latency Distribution')
    axs[1].set_xlabel('Request Latency (seconds)')
    axs[1].set_ylabel('Frequency')
    axs[1].grid(axis='y', linestyle='--')
    
    # --- Plot 3: Latency Box Plot ---
    axs[2].boxplot(latencies, vert=False, patch_artist=True, boxprops=dict(facecolor='lightblue'))
    axs[2].set_title('Latency Box Plot')
    axs[2].set_xlabel('Request Latency (seconds)')
    axs[2].grid(True)

    # Save the combined chart to a file
    chart_filename = 'full_analysis_report.png'
    fig.tight_layout(pad=3.0)
    plt.savefig(chart_filename)
    print(f"\nAnalysis chart saved as '{chart_filename}'")


async def run_test(url, num_requests):
    """Runs the load balancing test and generates visualizations."""
    tasks = []
    server_counts = Counter()
    all_latencies = []
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        for _ in range(num_requests):
            tasks.append(fetch(session, url))
            
        responses = await asyncio.gather(*tasks)
        
        for server_id, latency in responses:
            all_latencies.append(latency)
            if server_id:
                server_counts[server_id] += 1

    end_time = time.time()
    
    print(f"\nTest completed in {end_time - start_time:.2f} seconds.")
    
    # --- Print Load Distribution Results ---
    print("\n--- Request Distribution ---")
    total_requests_handled = 0
    if not server_counts:
        print("No successful requests were handled.")
    else:
        for server, count in sorted(server_counts.items()):
            print(f"  {server}: {count} requests")
            total_requests_handled += count
    
    print(f"\nTotal successful requests: {total_requests_handled}/{num_requests}")
    
    # --- Print Latency Statistics ---
    if all_latencies:
        print("\n--- Latency Statistics ---")
        print(f"  Average: {np.mean(all_latencies):.4f}s")
        print(f"  Median:  {np.median(all_latencies):.4f}s")
        print(f"  p99:     {np.percentile(all_latencies, 99):.4f}s")
        print(f"  Min:     {np.min(all_latencies):.4f}s")
        print(f"  Max:     {np.max(all_latencies):.4f}s")
    
    # --- Generate Visualizations ---
    generate_visualizations(server_counts, all_latencies, num_requests)

if __name__ == '__main__':
    LOAD_BALANCER_URL = "http://localhost:5000/home"
    NUM_REQUESTS = 10000
    
    # Make sure you have numpy installed: pip install numpy
    print(f"Starting test with {NUM_REQUESTS} async requests to {LOAD_BALANCER_URL}...")
    asyncio.run(run_test(LOAD_BALANCER_URL, NUM_REQUESTS))
