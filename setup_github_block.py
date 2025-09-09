#!/usr/bin/env python
# setup_github_block.py
import os
from prefect_github import GitHubCredentials

def create_github_block(token: str, block_name: str = "github-credentials"):
    """Create and save a GitHub credentials block"""
    github_credentials = GitHubCredentials(
        token=token,
    )
    github_credentials.save(name=block_name, overwrite=True)
    print(f"✅ GitHub credentials block '{block_name}' has been created/updated")

if __name__ == "__main__":
    # Get GitHub token from environment variable
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        raise ValueError(
            "GitHub token not found. Please set the GITHUB_TOKEN environment variable."
        )
    
    # Create the GitHub credentials block
    create_github_block(github_token)
    
    print("\nNow you can reference this block in your deployments using:")
    print("{{ prefect.blocks.github-credentials.github-credentials }}")
