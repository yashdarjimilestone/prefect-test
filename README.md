# Prefect on Kubernetes with GitHub Integration

This repository contains configuration for running Prefect Server in a Kubernetes cluster, with flows deployed from GitHub using Prefect's GitHub block.

## What You're Doing in This Setup

You are setting up Prefect Server on Kubernetes (self-hosted, not Prefect Cloud) and telling it to pull flow code from GitHub at runtime instead of packaging flows into Docker images or running them only from your local machine.

Think of it like this:

- Kubernetes runs the Prefect server + database (Postgres).
- GitHub stores your flow code (flows/my_flow.py).
- Your local machine is mainly used for setup (creating Prefect blocks, work pool, deployments).
- Prefect Worker runs inside Kubernetes (or locally) and executes flows by cloning them from GitHub.

✅ Local machine is only for setup and optional local worker execution.

### Simple Analogy

- Local machine = sets up the environment (like provisioning).
- GitHub repo = where your flow code lives.
- Kubernetes = runs Prefect server + DB + workers (the infrastructure).
- Worker = actually runs your flow by pulling the code from GitHub.

### Architecture Diagram

```
┌─────────────────┐     ┌──────────────────────────────────────┐
│                 │     │            Kubernetes Cluster         │
│   Local Machine │     │ ┌────────────┐      ┌──────────────┐ │
│   (Setup Only)  │     │ │            │      │              │ │
│                 │     │ │ PostgreSQL │◄─────┤ Prefect      │ │
│  - Create Blocks│     │ │ Database   │      │ Server       │ │
│  - Create Work  │     │ │            │      │              │ │
│    Pool         ├────►│ └────────────┘      └──────┬───────┘ │
│  - Create       │     │                            │         │
│    Deployment   │     │                            │         │
│                 │     │                            ▼         │
│                 │     │                     ┌─────────────┐  │
│                 │     │                     │ Prefect     │  │
│                 │     │                     │ Worker      │  │
└─────────────────┘     │                     │             │  │
                        │                     └──────┬──────┘  │
                        │                            │         │
                        └────────────────────────────┼─────────┘
                                                     │
                        ┌────────────────────────────▼─────────┐
                        │                                      │
                        │          GitHub Repository           │
                        │                                      │
                        │            - Flow Code               │
                        │            - Dependencies            │
                        │                                      │
                        └──────────────────────────────────────┘
```

## Overview

This setup allows you to:
- Run Prefect Server in a Kubernetes cluster
- Store flow metadata in PostgreSQL
- Pull flow code directly from GitHub repositories
- Execute flows using a local worker

## Prerequisites

- Kubernetes cluster with kubectl access
- Python 3.11+
- Prefect 3.4.11+
- GitHub repository with your flow code
- GitHub Personal Access Token with `repo` scope

## Step-by-Step Setup Guide

### 0. Initial Setup and Configuration

Set the Prefect API URL:

```bash
# Configure the Prefect API URL
prefect config set PREFECT_API_URL=http://localhost:4200/api
```

### 1. Create Kubernetes Namespace

If you need to clean up a previous setup:

```bash
# To clear resources in an existing namespace
kubectl delete -f Kubernetes/ -n prefect-test

# To delete the namespace completely
kubectl delete namespace prefect-test
```

Then create a fresh namespace:

```bash
kubectl create namespace prefect-test
```

### 2. Deploy PostgreSQL Database

```bash
kubectl apply -f Kubernetes/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n prefect-test --timeout=300s
```

### 3. Deploy Prefect Server

```bash
kubectl apply -f Kubernetes/prefect-server.yaml
kubectl wait --for=condition=ready pod -l app=prefect-server -n prefect-test --timeout=300s
```

### 4. Create Worker Service Account

```bash
kubectl apply -f Kubernetes/prefect-worker-sa.yaml
```

### 5. Set Up Port Forwarding

This allows you to access the Prefect UI locally. Run this in a new terminal as it will run continuously:

```bash
kubectl port-forward -n prefect-test svc/prefect-server 4200:4200
```

Verify the server is running:

```bash
curl http://localhost:4200/api/health
```

You should see a response with `true` and status code 200.

### 6. Create GitHub Credentials Block

First, set your GitHub token as an environment variable:

```bash
# PowerShell
$env:GITHUB_TOKEN = "your-github-token-here"

# Bash
# export GITHUB_TOKEN="your-github-token-here"
```

Then run the script to create the GitHub credentials block:

```bash
# Configure the Prefect API URL (if not already set)
prefect config set PREFECT_API_URL=http://localhost:4200/api

# Create the GitHub credentials block
python setup_github_block.py
```

You should see a confirmation that the block was created: `✅ GitHub credentials block 'github-credentials' has been created/updated`

### 7. Create a Work Pool

# Create the work pool

```bash
python setup_work_pool.py
```

This creates a process-based work pool named 'k8s-pool'.

### 8. Create a Deployment from GitHub

```bash
python github_deployment.py
```

This creates a deployment that pulls code from the GitHub repository specified in the prefect.yaml file.

### 9. Start a Worker

You have two options for running your worker:

#### Option A: Run the Worker Locally (for development/testing)

Start a worker that will poll for and execute flow runs on your local machine. Run this in a new terminal as it will run continuously:

```bash
# Option 1: Run directly in the terminal
prefect worker start --pool k8s-pool

# Option 2: Run with auto-restart script (recommended for local development)
python run_worker.py
```

The worker will connect to the Prefect server and watch for flow runs to execute. With this option, flows run on your local machine.

#### Option B: Deploy the Worker to Kubernetes (recommended for production)

##### 1. How Worker Deployment Works

We'll deploy a Prefect worker pod that runs inside your Kubernetes cluster.

##### 2. How Flow Execution Works Here

- Worker pod runs inside Kubernetes
- When a deployment is triggered, Prefect tells this worker
- Worker pod clones your flow from GitHub (using the GitHub block)
- Flow code runs inside this Kubernetes pod (not on your laptop)

##### 3. Apply the Worker Deployment

```bash
# Deploy the worker to Kubernetes
kubectl apply -f Kubernetes/prefect-worker.yaml -n prefect-test

# Verify the worker pod is running
kubectl get pods -n prefect-test
```

You should see a `prefect-worker-...` pod running.

##### 4. Check Worker Logs

```bash
# Check the worker logs
kubectl logs -f -n prefect-test deployment/prefect-worker
```

You should see something like:

```
Starting worker with pool 'k8s-pool'
Worker started!
```

This confirms that the worker is running inside Kubernetes and ready to execute flows.

### Important Note on Worker Execution

There's a key difference between local and Kubernetes worker execution:

**Local Worker Execution**:
- Code is executed on your local machine
- Local environment, dependencies, file system, etc.
- Useful for development and testing

**Kubernetes Worker Execution**:
- Code is executed inside the worker pod in Kubernetes
- Isolated environment with its own dependencies
- More suitable for production environments
- More scalable and better for high availability

For Kubernetes worker to work properly, make sure:
1. The Prefect server is accessible to the worker (listening on 0.0.0.0)
2. The GitHub credentials are properly configured
3. Any dependencies your flows need are listed in requirements.txt of your GitHub repo

### 10. Run the Deployment

```bash
prefect deployment run my-flow/github-poc
```

This will create a flow run that:
1. Pulls the code from GitHub
2. Installs requirements
3. Executes the flow

### 11. Using the Prefect API to Run Deployments

You can also trigger deployments programmatically using the Prefect API:

```bash
# First, get your deployment ID
curl -X POST "http://localhost:4200/api/deployments/filter" \
     -H "Content-Type: application/json" \
     -d '{"name": "github-poc"}'

# Then trigger a run using the deployment ID
curl -X POST "http://localhost:4200/api/deployments/<deployment-id>/create_flow_run" \
     -H "Content-Type: application/json" \
     -d '{
           "parameters": {},
           "tags": ["manual-trigger"]
         }'
```

The API endpoint is: `POST /deployments/{deployment_id}/create_flow_run`

This will return a JSON response with a `flow_run_id` that you can use to track the run.

## Verifying Your Setup

Check that your flow run completed successfully:

```bash
prefect flow-run ls
```

You should see your flow run with a COMPLETED state.

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃                                   ID ┃ Flow    ┃ Name               ┃ State     ┃ When          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 41d04580-5731-497e-b1d9-13ab9391bd01 │ my-flow │ intelligent-beetle │ COMPLETED │ 5 minutes ago │
└──────────────────────────────────────┴─────────┴────────────────────┴───────────┴───────────────┘
```

You can view the logs of a completed flow run:

```bash
prefect flow-run logs <FLOW_RUN_ID>
```

### Verifying Kubernetes Worker Execution

When running a worker in Kubernetes, you can verify that the worker is successfully picking up and executing flow runs by:

1. Check the worker logs:
   ```bash
   kubectl logs -n prefect-test deployment/prefect-worker
   ```

2. Look for log entries like:
   ```
   Discovered type 'process' for work pool 'k8s-pool'.
   Worker 'ProcessWorker 135d61f0-7dde-47cc-8369-7a8a4ab0a51f' started!
   11:36:15.890 | INFO    | prefect.flow_runs.worker - Worker 'ProcessWorker 135d61f0-7dde-47cc-8369-7a8a4ab0a51f' submitting flow run 'e1a9b2b6-2df3-47c1-880e-b30ed999db88'
   11:36:16.910 | INFO    | prefect.flow_runs.runner - Opening process...
   11:36:17.010 | INFO    | prefect.flow_runs.worker - Completed submission of flow run 'e1a9b2b6-2df3-47c1-880e-b30ed999db88'
   11:36:20.528 | INFO    | Flow run 'analytic-mammoth' -  > Running git_clone step...
   11:36:21.478 | INFO    | Flow run 'analytic-mammoth' - Beginning flow run 'analytic-mammoth' for flow 'my-flow'
   11:36:21.479 | INFO    | Flow run 'analytic-mammoth' - View at http://prefect-server:4200/runs/flow-run/e1a9b2b6-2df3-47c1-880e-b30ed999db88
   11:36:21.624 | INFO    | Task run 'say_hello-fdd' - Hello, world!
   11:36:21.630 | INFO    | Task run 'say_hello-fdd' - Finished in state Completed()
   11:36:21.826 | INFO    | Task run 'data_processing-6b9' - Starting data processing for Hello world
   11:36:21.827 | INFO    | Task run 'data_processing-6b9' - Processing will take 104 seconds...
   ```

These logs confirm that:
- The worker successfully connected to the Prefect server
- The worker picked up a flow run 
- The worker cloned the flow code from GitHub
- The worker executed the flow successfully

You can also view details and logs in the Prefect UI at http://localhost:4200.

## Project Structure

- `flows/`: Contains the flow code
- `Kubernetes/`: Contains Kubernetes manifests for Prefect server and worker
  - `postgres.yaml`: PostgreSQL database deployment
  - `prefect-server.yaml`: Prefect server deployment and service
  - `prefect-worker-sa.yaml`: Service account for Prefect worker
  - `prefect-worker.yaml`: Prefect worker deployment (optional)
- `setup_github_block.py`: Script to create the GitHub credentials block
- `setup_work_pool.py`: Script to create the Kubernetes work pool
- `github_deployment.py`: Script to create a deployment that pulls code from GitHub
- `run_worker.py`: Script to run a worker with automatic restart capability
- `Kubernetes/prefect-worker.yaml`: Kubernetes deployment for running the Prefect worker in the cluster

## Running Multiple Flow Runs

You can trigger multiple flow runs in a loop using PowerShell:

```powershell
# Run multiple flow runs in a loop
$count = 0
while ($count -lt 10) {
    prefect deployment run my-flow/github-poc
    $count++
    Write-Host "Run $count of 10 completed"
    Start-Sleep -Milliseconds 500
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Ensure port forwarding is active
   - Check that the Prefect server pod is running with `kubectl get pods -n prefect-test`

2. **GitHub Authentication Issues**:
   - Verify your GitHub token has the correct permissions
   - Ensure the token environment variable is set correctly

3. **Worker Not Connecting**:
   - Check that the worker can reach the Prefect server
   - Verify the work pool exists with `prefect work-pool ls`
   - For Kubernetes worker: check pod status with `kubectl get pods -n prefect-test` and logs with `kubectl logs -n prefect-test deployment/prefect-worker`
   - If you see "All connection attempts failed" in worker logs, ensure the Prefect server is listening on all interfaces:
     ```yaml
     # In prefect-server.yaml, ensure the args include "--host 0.0.0.0"
     args: ["prefect", "server", "start", "--host", "0.0.0.0"]
     ```

4. **Flow Run Fails**:
   - Check for errors in the flow run logs with `prefect flow-run logs <FLOW_RUN_ID>`
   - Verify the GitHub repository and branch are correct in prefect.yaml
   - Check that your requirements.txt has all needed dependencies

### Viewing Kubernetes Logs

For deeper troubleshooting, you can check the logs of Kubernetes pods:

```bash
# Check pod status in the namespace
kubectl get pods -n prefect-test

# Check Prefect server logs
kubectl logs -n prefect-test <prefect-server-pod-name>

# Check Postgres logs
kubectl logs -n prefect-test <postgres-pod-name>

# Check Prefect worker logs (if deployed in Kubernetes)
kubectl logs -n prefect-test <prefect-worker-pod-name>
```

You can check the status of your work pools with:

```bash
prefect work-pool ls
```

Example output:
```
                                   Work Pools
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Name     ┃ Type    ┃                                   ID ┃ Concurrency Limit ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ k8s-pool │ process │ b271a8cc-fb6b-4b4a-901f-91f2d865e754 │ None              │
└──────────┴─────────┴──────────────────────────────────────┴───────────────────┘
```

- **Prefect Worker**: Polls for flows to run, uses a Kubernetes service account
- **Flow Storage**: Flows are stored in GitHub and pulled at runtime
- **Authentication**: Local Prefect Server uses no authentication (suitable for development)

## Complete Cleanup

To completely remove everything created by this setup:

```bash
# Delete all resources in the namespace
kubectl delete -f Kubernetes/ -n prefect-test

# Delete the entire namespace
kubectl delete namespace prefect-test

# To clean Prefect-related resources if needed
prefect work-pool delete k8s-pool --yes
prefect block delete github-credentials
```

## Important Components

- `prefect.yaml`: Defines how flows are pulled from GitHub
- `deploy.py`: Creates GitHub credentials block and deployment
- `flows/my_flow.py`: Example flow to be executed
- `Kubernetes/`: Contains all Kubernetes manifests

## Data Flow

```
┌─────────────────┐     ┌───────────────────┐    ┌────────────────────┐
│                 │     │                   │    │                    │
│ User / UI       │─────► Prefect Server    │◄───┤ Prefect Database   │
│                 │     │                   │    │                    │
└────────┬────────┘     └──────────┬────────┘    └────────────────────┘
         │                         │
         │                         │
         │                         │
         │                         ▼
         │               ┌───────────────────┐    ┌────────────────────┐
         │               │                   │    │                    │
         └──────────────►│ Prefect Worker    │◄───┤ GitHub Repo        │
                         │                   │    │                    │
                         └──────────┬────────┘    └────────────────────┘
                                    │
                                    │
                                    ▼
                         ┌───────────────────┐
                         │                   │
                         │ Flow Execution    │
                         │                   │
                         └───────────────────┘
```

## Running Flows

Once deployed, flows can be run from the Prefect UI or via the Prefect API.
