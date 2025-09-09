import subprocess
import time
import sys
import os
import signal

def signal_handler(sig, frame):
    print("\nExiting worker monitoring script...")
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_worker():
    print("Starting Prefect worker for k8s-pool...")
    
    while True:
        try:
            # Start the worker process
            process = subprocess.Popen(
                ["prefect", "worker", "start", "--pool", "k8s-pool"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Print output in real-time
            for line in process.stdout:
                print(line, end='')
            
            # Wait for process to complete
            process.wait()
            print(f"Worker exited with code {process.returncode}")
            
        except Exception as e:
            print(f"Error running worker: {e}")
        
        print("Restarting worker in 10 seconds...")
        time.sleep(10)

if __name__ == "__main__":
    start_worker()
