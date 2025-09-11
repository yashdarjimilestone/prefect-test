#!/usr/bin/env python
# github_deployment.py
import os
from prefect import flow
from prefect.runner.storage import GitRepository
from prefect_github import GitHubCredentials

def create_github_deployment():
    """
    Create a deployment that pulls code from GitHub.
    
    This deployment will:
    1. Clone the repository specified in prefect.yaml
    2. Install requirements from requirements.txt
    3. Run the flow specified in the entrypoint
    """
    # Load the GitHub credentials
    github_credentials = GitHubCredentials.load("github-credentials")
    
    # Define the GitHub repository source
    source = GitRepository(
        url="https://github.com/yashdarjimilestone/prefect-test.git",
        credentials=github_credentials
    )
    
    # Create and register the deployment
    flow.from_source(
        source=source, 
        entrypoint="flows/my_flow.py:my_flow"
    ).deploy(
        name="github-poc",
        work_pool_name="k8s-pool-k8s",
    )
    
    print("✅ Deployment 'my-flow/github-poc' has been created successfully")
    print("\nYou can run this deployment with:")
    print("prefect deployment run my-flow/github-poc")

if __name__ == "__main__":
    # Check if the GitHub token is set (not strictly necessary since we're loading the credentials)
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Warning: GITHUB_TOKEN environment variable is not set.")
        print("The deployment will try to use the existing 'github-credentials' block.")
    
    # Create the deployment
    create_github_deployment()
