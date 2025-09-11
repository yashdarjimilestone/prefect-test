"""
Script to perform a scaling analysis with Prefect
"""
import time
import subprocess
import datetime
import re
import uuid
import json

def submit_flows(count=4, delay=0.5):
    """Submit multiple flow runs and track their completion"""
    flow_run_ids = []
    flow_run_names = []
    run_tag = str(uuid.uuid4())[:8]  # Generate a unique tag for this batch
    start_time = time.time()
    
    print(f"Submitting {count} flow runs with tag: {run_tag}...")
    
    for i in range(count):
        # Submit flow run with a unique tag to help us track it
        result = subprocess.run(
            ["prefect", "deployment", "run", "my-flow/github-poc", "--param", f"tag={run_tag}-{i}"],
            capture_output=True,
            text=True
        )
        
        output = result.stdout
        print(f"Run submission output: {output}")
        
        # Extract flow run ID and name
        if "Created flow run '" in output:
            flow_name = output.split("Created flow run '")[1].split("'")[0]
            flow_run_names.append(flow_name)
            
            # Extract UUID from output
            uuid_match = re.search(r'UUID: ([0-9a-f-]+)', output)
            if uuid_match:
                flow_id = uuid_match.group(1)
                flow_run_ids.append(flow_id)
                print(f"Submitted flow run #{i+1}: {flow_name} (ID: {flow_id})")
        
        if i < count - 1:
            time.sleep(delay)
    
    submit_duration = time.time() - start_time
    print(f"Submitted {count} flow runs in {submit_duration:.2f} seconds")
    print(f"Flow run IDs: {flow_run_ids}")
    print(f"Flow run names: {flow_run_names}")
    
    # Now wait for completion and monitor status
    wait_start = time.time()
    max_wait_time = 300  # 5 minutes maximum wait time
    check_interval = 5   # Check every 5 seconds
    completed = 0
    
    print("\nWaiting for flow runs to complete...")
    
    while completed < count and (time.time() - wait_start) < max_wait_time:
        completed = 0
        running = 0
        pending = 0
        scheduled = 0
        
        # Check each flow run individually
        for flow_id in flow_run_ids:
            try:
                # Use the Prefect API to get flow run status
                result = subprocess.run(
                    ["prefect", "flow-run", "inspect", flow_id],
                    capture_output=True,
                    text=True
                )
                
                output = result.stdout
                
                if "State:     COMPLETED" in output:
                    completed += 1
                elif "State:     RUNNING" in output:
                    running += 1
                elif "State:     PENDING" in output:
                    pending += 1
                elif "State:     SCHEDULED" in output:
                    scheduled += 1
            except Exception as e:
                print(f"Error checking flow run {flow_id}: {e}")
        
        print(f"Status: Completed={completed}/{count}, Running={running}, Pending={pending}, Scheduled={scheduled}")
        
        if completed == count:
            break
            
        time.sleep(check_interval)
    
    total_time = time.time() - start_time
    print(f"\nFlow runs: {completed}/{count} completed in {total_time:.2f} seconds")
    
    return {
        "total_time": total_time,
        "submit_time": submit_duration,
        "completed": completed,
        "total_runs": count
    }

def measure_scaling(worker_counts=[1, 2, 3], flow_count=4):
    """Measure performance with different worker counts"""
    results = {}
    
    for worker_count in worker_counts:
        print(f"\n{'='*20}")
        print(f"SCALING TO {worker_count} WORKERS")
        print(f"{'='*20}")
        
        # Scale the worker deployment
        subprocess.run(
            ["kubectl", "scale", "deployment", "prefect-worker", 
             f"--replicas={worker_count}", "-n", "prefect-test"],
            check=True
        )
        
        # Wait for scaling to take effect
        print(f"Waiting for {worker_count} workers to be ready...")
        time.sleep(20)  # Give time for workers to start
        
        # Verify worker count
        result = subprocess.run(
            ["kubectl", "get", "deployment", "prefect-worker", "-n", "prefect-test"],
            capture_output=True,
            text=True
        )
        print(f"Worker deployment status:\n{result.stdout}")
        
        # Run the test
        print(f"\nRunning test with {worker_count} workers...")
        result = submit_flows(flow_count)
        results[worker_count] = result
        
        print(f"\nResults with {worker_count} workers:")
        print(f"Total time: {result['total_time']:.2f} seconds")
        print(f"Submit time: {result['submit_time']:.2f} seconds")
        print(f"Completion rate: {result['completed']}/{result['total_runs']}")
    
    # Print summary
    print("\n{'='*40}")
    print("SCALING ANALYSIS SUMMARY")
    print("{'='*40}")
    
    for worker_count, result in results.items():
        print(f"{worker_count} workers: {result['total_time']:.2f} seconds, " 
              f"Completion: {result['completed']}/{result['total_runs']}")
    
    return results

if __name__ == "__main__":
    print(f"=== SCALING ANALYSIS: {datetime.datetime.now()} ===")
    measure_scaling(worker_counts=[1, 2, 3], flow_count=4)
