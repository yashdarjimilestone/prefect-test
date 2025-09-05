#!/usr/bin/env python
# setup_work_pool.py
import os
import sys
import time
from prefect.client import get_client

async def create_k8s_work_pool():
    """Create a Kubernetes work pool for Prefect if it doesn't exist"""
    client = get_client()
    
    # Check if the work pool already exists
    work_pools = await client.read_work_pools()
    existing_pools = [pool.name for pool in work_pools]
    
    if "k8s-pool" in existing_pools:
        print("Work pool 'k8s-pool' already exists.")
        return
    
    print("Creating Kubernetes work pool 'k8s-pool'...")
    
    # Create a Process work pool (standard type for Kubernetes workers)
    await client.create_work_pool(
        name="k8s-pool",
        work_queue_name="default",
        type="process",
        description="Kubernetes worker pool"
    )
    
    print("Work pool 'k8s-pool' created successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_k8s_work_pool())
