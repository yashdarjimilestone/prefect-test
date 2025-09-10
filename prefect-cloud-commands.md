# 🚀 Prefect Cloud Commands (uvx CLI)

## 1. Log in to Prefect Cloud

```bash
uvx prefect-cloud login
```

Follow the prompt → paste your **Prefect Cloud API key**.

## 2. Connect to GitHub

```bash
uvx prefect-cloud github setup
```

This will open a browser (or ask for a GitHub PAT) to link your repo access.

## 3. Deploy Your Flow

From the **root of your repo** (where `flows/my_flow.py` lives):

```bash
uvx prefect-cloud deploy flows/my_flow.py:my_flow --from yashdarjimilestone/prefect-test --name github-poc
```

* `flows/my_flow.py:my_flow` → file and flow function name
* `--from yashdarjimilestone/prefect-test` → your GitHub repo
* `--name github-poc` → deployment name

## 4. Run Your Deployment

```bash
uvx prefect-cloud run my_flow/github-poc
```

You can run it multiple times to see concurrent flow runs:

```bash
# Run multiple flow runs in a loop (PowerShell)
$count = 0
while ($count -lt 10) {
    uvx prefect-cloud run my_flow/github-poc
    $count++
    Write-Host "Run $count of 10 completed"
    Start-Sleep -Milliseconds 500
}
```

## 5. (Optional) Schedule It

Run every hour:

```bash
uvx prefect-cloud schedule my_flow/github-poc "0 * * * *"
```

Remove schedule:

```bash
uvx prefect-cloud unschedule my_flow/github-poc
```

Delete deployment:

```bash
uvx prefect-cloud delete my_flow/github-poc
```

## Additional Options

### Check Workspace and User Information

```bash
# Get workspace and account information
uvx prefect-cloud whoami
```

### Passing Parameters to Deployments

To run a deployment with parameters:

```bash
uvx prefect-cloud run my_flow/github-poc -p param1=value1 -p param2=value2
```

For JSON parameters:

```bash
uvx prefect-cloud run my_flow/github-poc -p "config={'key': 'value', 'items': [1, 2, 3]}"
```

### View Logs

For viewing flow run logs, you'll need to use the standard Prefect CLI:

```bash
# List recent flow runs (limit to 100 results)
prefect flow-run ls --limit 100

# Get detailed logs for a specific flow run (use the flow run ID)
prefect flow-run logs "068c1502-2654-7dd4-8000-7f53fad16267"

# Count the number of flow runs
prefect flow-run ls --limit 100 | Select-String -Pattern "my_flow" | Measure-Object | Select-Object -ExpandProperty Count
```

### List Deployments

```bash
uvx prefect-cloud ls
```

## Understanding Concurrency in Prefect

### 1️⃣ Flow-Level Concurrency

When you run multiple instances of the same deployment:

```bash
uvx prefect-cloud run my_flow/github-poc
uvx prefect-cloud run my_flow/github-poc
```

* Prefect creates multiple independent flow runs from the same deployment
* Each run executes concurrently if your workers have capacity
* Prefect auto-generates unique names (like "chirpy-hummingbird", "olive-anaconda")
* You can set custom names with `--run-name`

👉 This is parallelism at the flow run level.

### 2️⃣ Task-Level Concurrency

Within a single flow run, tasks can execute concurrently:

* By default, Prefect uses a `ConcurrentTaskRunner` which runs tasks in parallel threads
* Example: An ingestion flow downloading from 10 URLs can fan out tasks to execute concurrently

👉 This is parallelism at the task level.

### 3️⃣ Controlling Concurrency

Prefect Cloud provides mechanisms to limit concurrency and prevent overload:

#### Work Pool Concurrency

Limit how many flow runs can execute simultaneously per pool:

```bash
uvx prefect-cloud work-pool set-concurrency default-agent-pool 3
```

* With this limit, at most 3 flows will run at once
* Additional flow runs wait in "Pending" state
* Example: After setting this limit and running 5 flow runs, 3 will execute in parallel while 2 wait in queue

#### Tag-based Concurrency

You can tag runs (e.g., with client names) and set max concurrency per tag:

* Example: Only 1 run at a time for "client-a", while others run freely
* This allows granular control over resource allocation

### 4️⃣ Scaling in Prefect Cloud

Prefect Cloud handles orchestration while you control the workers:

* A single worker process can run a limited number of flows (depends on runner type)
* To scale out:
  * Start more worker processes (on your laptop, VMs, Kubernetes, etc.)
  * All workers connect to the same work pool
  * Prefect Cloud distributes runs across all available workers

#### Autoscaling

In cloud environments (Kubernetes, ECS, etc.), you can configure autoscaling for worker pods/containers:

* Worker infrastructure can automatically scale based on demand
* Prefect Cloud continues to orchestrate regardless of worker count

## Monitoring Flow Runs in Detail

To get more insights into your flow runs, you can use the following commands:

### Inspect a Specific Flow Run

```bash
# View details about a specific flow run
prefect flow-run inspect "068c1502-2654-7dd4-8000-7f53fad16267"
```

### Filter Flow Runs

```bash
# List runs with a specific state (e.g., COMPLETED, FAILED, RUNNING)
prefect flow-run ls --state COMPLETED

# List runs for a specific deployment name
prefect flow-run ls --deployment-name "github-poc"
```

### Cancel or Delete Flow Runs

```bash
# Cancel a running flow
prefect flow-run cancel "068c1502-2654-7dd4-8000-7f53fad16267"

# Delete a flow run
prefect flow-run delete "068c1502-2654-7dd4-8000-7f53fad16267"
```

### Access Prefect Cloud UI

For a visual interface, access your Prefect Cloud dashboard:

```bash
# Get the dashboard URL
uvx prefect-cloud whoami | Select-String -Pattern "Dashboard"
```
