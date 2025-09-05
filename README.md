# Prefect on Kubernetes

This repository contains configuration for running Prefect Server in a Kubernetes cluster, with flows deployed from GitHub.

## Setup Instructions

### 1. Deploy Prefect Server to Kubernetes

First, ensure you have kubectl configured to access your Kubernetes cluster.

```bash
# Create namespace if it doesn't exist
kubectl create namespace data-ingestion

# Deploy PostgreSQL database for Prefect
kubectl apply -f Kubernetes/postgres.yaml

# Deploy Prefect Server
kubectl apply -f Kubernetes/prefect-server.yaml

# Create worker service account with permissions
kubectl apply -f Kubernetes/prefect-worker-sa.yaml

# Deploy Prefect Worker
kubectl apply -f Kubernetes/prefect-worker.yaml

# Optional: Deploy ingress if you need external access
kubectl apply -f Kubernetes/prefect-ingress.yaml
```

### 2. Set up GitHub Secrets

In your GitHub repository, add the following secrets:

- `PREFECT_API_URL`: URL to your Prefect Server API (e.g., `http://your-ingress-host/api` if using ingress, or use port-forwarding)
- `GITHUB_TOKEN`: A GitHub token with repo access to clone the repository

### 3. Initial Deployment

For the first deployment, you can either:

- Push to the main branch to trigger the GitHub Action
- Or manually run:

```bash
# Install dependencies
pip install "prefect[github]" prefect-github

# Create work pool and deploy
python setup_work_pool.py
python deploy.py
```

## Architecture

- **Prefect Server**: Runs in Kubernetes, using PostgreSQL for storage
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
