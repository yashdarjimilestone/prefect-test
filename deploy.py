# deploy.py
import os
from prefect import flow
from prefect.runner.storage import GitRepository
from prefect_github import GitHubCredentials

# 1) Create / save a GitHubCredentials block (only needs to be done once).
def create_github_block(token: str, block_name: str = "github-token"):
    creds = GitHubCredentials(token=token)
    creds.save(name=block_name, overwrite=True)
    print(f"Saved GitHubCredentials block: {block_name}")

if __name__ == "__main__":
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        raise RuntimeError("Set GITHUB_TOKEN environment variable (used to create the GitHubCredentials block).")

    # Save the block to Prefect
    create_github_block(GITHUB_TOKEN, block_name="github-token")

    # create a deployment referencing the repo (optional: you can use prefect.yaml approach instead)
    # If you want to register deployments from Python instead of prefect.yaml, you can use:
    source = GitRepository(
        url="https://github.com/yashdarjimilestone/prefect-test.git",
        credentials=GitHubCredentials.load("github-token")
    )

    # Use flow.from_source(...).deploy(...) as a one-liner to create the deployment:
    # Note: entrypoint format is "path/to/file.py:flow_name"
    flow.from_source(source=source, entrypoint="flows/my_flow.py:my_flow").deploy(
        name="github-poc",
        work_pool_name="k8s-pool",
    )
    print("Deployment created: github-poc")
