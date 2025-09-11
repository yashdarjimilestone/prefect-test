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

Create a Kubernetes work pool for better scaling and resource isolation:

```bash
prefect work-pool create k8s-pool-k8s --type kubernetes
```

#### Important: Configure Work Pool Job Template

The default job template needs to be updated to properly support GitHub integration. Create a `job_template.json` file with the following content:

```json
{
  "job_configuration": {
    "job_manifest": {
      "apiVersion": "batch/v1",
      "kind": "Job",
      "metadata": {
        "generateName": "prefect-job-"
      },
      "spec": {
        "completions": 1,
        "parallelism": 1,
        "template": {
          "spec": {
            "serviceAccountName": "prefect-worker",
            "containers": [
              {
                "name": "prefect-job",
                "image": "prefecthq/prefect:3.4.11-python3.11",
                "command": ["bash", "-c"],
                "args": ["pip install prefect-github && python -m prefect.engine"],
                "env": [
                  {
                    "name": "GITHUB_TOKEN",
                    "valueFrom": {
                      "secretKeyRef": {
                        "name": "github-token",
                        "key": "token"
                      }
                    }
                  },
                  {
                    "name": "PREFECT_GITHUB_CREDENTIALS",
                    "value": "github-credentials"
                  },
                  {
                    "name": "PREFECT_API_URL",
                    "value": "http://prefect-server:4200/api"
                  }
                ]
              }
            ],
            "restartPolicy": "Never"
          }
        },
        "backoffLimit": 0
      }
    },
    "namespace": "prefect-test"
  },
  "variables": {
    "type": "object",
    "properties": {}
  }
}
```

Then update the work pool with this job template:

```bash
prefect work-pool update k8s-pool-k8s --base-job-template job_template.json
```

This configuration ensures that:
1. The GitHub token is available to the job from Kubernetes secrets
2. The job uses the GitHub credentials block via the `PREFECT_GITHUB_CREDENTIALS` environment variable
3. The job installs the necessary `prefect-github` package
4. The job has the correct permissions to clone repositories


### 8. Create a Deployment from GitHub

```bash
python github_deployment.py
```

This creates a deployment that pulls code from the GitHub repository specified in the prefect.yaml file.

### 9. Deploy the Worker to Kubernetes

##### 1. How Worker Deployment Works

We'll deploy a Prefect worker pod that runs inside your Kubernetes cluster.

##### 2. How Flow Execution Works

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
Worker 'KubernetesWorker <worker-id>' started!
```

This confirms that the worker is running inside Kubernetes and ready to execute flows.

### 10. Run the Deployment

First, set up a Kubernetes secret for your GitHub token (critical for the GitHub integration to work):

For PowerShell (using the environment variable you set earlier):
```powershell
kubectl create secret generic github-token --from-literal=token=$env:GITHUB_TOKEN -n prefect-test
```

> **IMPORTANT**: This step is crucial! Without this secret, flow runs will fail with "fatal: not a git repository" errors. The secret must be named `github-token` and have a key called `token` containing your GitHub personal access token.

Make sure your deployment is configured to use the Kubernetes work pool (should already be set in github_deployment.py):

```python
flow.from_source(
    source=source, 
    entrypoint="flows/my_flow.py:my_flow"
).deploy(
    name="github-poc",
    work_pool_name="k8s-pool-k8s",
)
```

Then run the deployment:

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

### Verifying Worker Execution

When running a worker in Kubernetes, you can verify that the worker is successfully picking up and executing flow runs by:

1. Check the worker logs:
   ```bash
   kubectl logs -n prefect-test deployment/prefect-worker
   ```

2. Look for log entries like:
   ```
   Worker 'KubernetesWorker <worker-id>' started!
   INFO | prefect.flow_runs.worker - Worker 'KubernetesWorker <worker-id>' submitting flow run '<flow-run-id>'
   INFO | prefect.flow_runs.worker - Creating Kubernetes job...
   INFO | prefect.flow_runs.worker - Completed submission of flow run '<flow-run-id>'
   INFO | Flow run '<flow-name>' -  > Running git_clone step...
   INFO | Flow run '<flow-name>' - Beginning flow run '<flow-name>' for flow 'my-flow'
   ```

These logs confirm that:
- The worker successfully connected to the Prefect server
- The worker picked up a flow run 
- The worker created a Kubernetes job
- The job cloned the flow code from GitHub
- The flow execution has started

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
   - For Kubernetes work pools, make sure your GitHub token is stored as a Kubernetes secret

3. **Worker Not Connecting**:
   - Check that the worker can reach the Prefect server
   - Verify the work pool exists with `prefect work-pool ls`
   - For Kubernetes worker: check pod status with `kubectl get pods -n prefect-test` and logs with `kubectl logs -n prefect-test deployment/prefect-worker`
   - If you see "All connection attempts failed" in worker logs, ensure the Prefect server is listening on all interfaces:
     ```yaml
     # In prefect-server.yaml, ensure the args include "--host 0.0.0.0"
     args: ["prefect", "server", "start", "--host", "0.0.0.0"]
     ```

4. **Git Repository Errors in Kubernetes Jobs**:
   - If you see `fatal: not a git repository` errors, this is a common issue with GitHub integration in Kubernetes jobs. Here's how to fix it:
     
     **Root cause**: The Kubernetes job doesn't have the proper configuration to access GitHub and clone repositories.
     
     **Solution**:
     1. Make sure you have a Kubernetes secret with your GitHub token:
        ```bash
        kubectl create secret generic github-token --from-literal=token=your-github-token-here -n prefect-test
        ```
     
     2. Update your work pool job template to include:
        - The `GITHUB_TOKEN` environment variable from the Kubernetes secret
        - The `PREFECT_GITHUB_CREDENTIALS` environment variable set to your block name
        - Command to install the `prefect-github` package
        - Proper job configuration with `completions` and `parallelism` settings
     
     3. Apply the updated job template to your work pool:
        ```bash
        prefect work-pool update k8s-pool-k8s --base-job-template job_template.json
        ```
     
     4. For reference, see the job template example in section 7 of this README.
   
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
prefect work-pool delete k8s-pool-k8s --yes
prefect block delete github-credentials
```

## Performance Considerations

When running Prefect in a Kubernetes environment, consider the following performance optimizations:

1. **Resource Allocation**: Adjust the CPU and memory requests/limits in `prefect-worker.yaml` and `job_template.json` based on your flow's requirements:
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "200m"
     limits:
       memory: "1Gi"
       cpu: "1000m"
   ```

2. **Worker Scaling**: For production environments, consider setting up Horizontal Pod Autoscaling for the worker:
   ```bash
   kubectl autoscale deployment prefect-worker -n prefect-test --min=1 --max=5 --cpu-percent=80
   ```

3. **Database Persistence**: For production, add a PersistentVolumeClaim to the PostgreSQL deployment to ensure data survives pod restarts.

4. **Flow Run Concurrency**: Adjust the work pool concurrency limit to control how many flow runs can execute simultaneously:
   ```bash
   prefect work-pool update k8s-pool-k8s --concurrency-limit 5
   ```

## Security Best Practices

1. **Token Security**: Never store your GitHub token in plain text in your codebase. Use environment variables or Kubernetes secrets.

2. **Network Security**: For production deployments, consider:
   - Enabling TLS for the Prefect server
   - Setting up proper network policies to restrict pod communication
   - Using Kubernetes namespaces for isolation

3. **Repository Access**: Use fine-grained GitHub access tokens with access only to necessary repositories.

4. **Secret Rotation**: Periodically rotate your GitHub tokens and update the Kubernetes secret:
   ```bash
   kubectl create secret generic github-token --from-literal=token=your-new-token-here -n prefect-test --dry-run=client -o yaml | kubectl apply -f -
   ```

## Extending This Setup

### Adding Flow Parameters

You can pass parameters to your flow when triggering a run:

```bash
prefect deployment run my-flow/github-poc -p name="custom-parameter"
```

Or via the API:

```bash
curl -X POST "http://localhost:4200/api/deployments/<deployment-id>/create_flow_run" \
     -H "Content-Type: application/json" \
     -d '{
           "parameters": {"name": "custom-parameter"},
           "tags": ["custom-run"]
         }'
```

### Setting Up Schedules

You can add a schedule to your deployment to run flows automatically:

```python
# In github_deployment.py
flow.from_source(
    source=source, 
    entrypoint="flows/my_flow.py:my_flow"
).deploy(
    name="github-poc",
    work_pool_name="k8s-pool-k8s",
    interval=3600  # Run every hour
)
```

### Adding Monitoring and Alerting

For production environments, consider setting up:
- Prometheus and Grafana for monitoring
- Prefect's notification system for alerts on flow run failures
- Integration with Slack, Teams, or email for notifications

## Important Components

- `prefect.yaml`: Defines how flows are pulled from GitHub
- `github_deployment.py`: Creates a deployment that pulls code from GitHub
- `setup_github_block.py`: Sets up the GitHub credentials block
- `flows/my_flow.py`: Example flow to be executed
- `Kubernetes/`: Contains all Kubernetes manifests
- `job_template.json`: Defines how flow runs execute in Kubernetes

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
