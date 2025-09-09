#!/usr/bin/env python
# setup_work_pool.py
import os
import sys
import time
from prefect.client.orchestration import get_client
from prefect.client.schemas.objects import WorkPool
from prefect.exceptions import ObjectAlreadyExists

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
    new_pool = WorkPool(
        name="k8s-pool",
        type="process",
        description="Kubernetes worker pool"
    )
    
    # Create the work pool
    await client.create_work_pool(work_pool=new_pool)
    
    # Create a default queue for the work pool if it doesn't exist
    try:
        await client.create_work_queue(
            name="default",
            work_pool_name="k8s-pool"
        )
        print("Default queue created for 'k8s-pool'.")
    except ObjectAlreadyExists:
        print("Default queue already exists for 'k8s-pool'.")
    
    print("Work pool 'k8s-pool' created successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_k8s_work_pool())
