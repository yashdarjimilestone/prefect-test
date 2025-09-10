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

```bash
uvx prefect-cloud logs my_flow/github-poc
```

### List Deployments

```bash
uvx prefect-cloud deployments
```
