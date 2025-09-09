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

### 1. Create Kubernetes Namespace

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
python setup_github_block.py
```

You should see a confirmation that the block was created: `✅ GitHub credentials block 'github-credentials' has been created/updated`

### 7. Create a Work Pool

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

Start a worker that will poll for and execute flow runs. Run this in a new terminal as it will run continuously:

```bash
# Option 1: Run directly in the terminal
prefect worker start --pool k8s-pool

# Option 2: Run with auto-restart script (recommended for local development)
python run_worker.py
```

The worker will connect to the Prefect server and watch for flow runs to execute.

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

4. **Flow Run Fails**:
   - Check for errors in the flow run logs
   - Verify the GitHub repository and branch are correct in prefect.yaml
- **Prefect Worker**: Polls for flows to run, uses a Kubernetes service account
- **Flow Storage**: Flows are stored in GitHub and pulled at runtime
- **Authentication**: Local Prefect Server uses no authentication (suitable for development)

## Important Components

- `prefect.yaml`: Defines how flows are pulled from GitHub
- `deploy.py`: Creates GitHub credentials block and deployment
- `flows/my_flow.py`: Example flow to be executed
- `Kubernetes/`: Contains all Kubernetes manifests

## Running Flows

Once deployed, flows can be run from the Prefect UI or via the Prefect API.
