# flows/my_flow.py
from prefect import flow, task
import time
import random
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=5))
def say_hello(name: str):
    print(f"Hello, {name}!")
    return f"Hello {name}"

@task
def data_processing(data: str):
    """Simulate data processing with a random delay between 10-20 seconds"""
    print(f"Starting data processing for {data}")
    delay = random.randint(30, 40)  # Random delay between 10-20 seconds
    print(f"Processing will take {delay} seconds...")
    time.sleep(delay)
    result = f"Processed data: {data.upper()}"
    print(f"Finished processing: {result}")
    return result

@task
def data_enrichment(processed_data: str):
    """Simulate data enrichment with a delay of 5-10 seconds"""
    print(f"Starting data enrichment for {processed_data}")
    delay = random.randint(10, 20)  # Delay between 5-10 seconds
    print(f"Enrichment will take {delay} seconds...")
    time.sleep(delay)
    result = f"{processed_data} [ENRICHED]"
    print(f"Finished enrichment: {result}")
    return result

@task
def data_validation(data: str):
    """Simulate validation with a delay of 15-25 seconds"""
    print(f"Starting validation for {data}")
    delay = random.randint(15, 25)  # Delay between 15-25 seconds
    print(f"Validation will take {delay} seconds...")
    time.sleep(delay)
    result = f"Validation passed for: {data}"
    print(f"Finished validation: {result}")
    return result

@task
def final_processing(enriched_data: str, validation_result: str):
    """Final processing task that depends on both enrichment and validation"""
    print(f"Starting final processing with inputs:")
    print(f"- Enriched data: {enriched_data}")
    print(f"- Validation result: {validation_result}")
    delay = random.randint(40, 55)  # Delay between 10-15 seconds
    print(f"Final processing will take {delay} seconds...")
    time.sleep(delay)
    result = f"FINAL RESULT: {enriched_data} ✓ {validation_result}"
    print(f"Final result: {result}")
    return result

@flow(log_prints=True)
def my_flow(name: str = "world", tag: str = None):
    # Print the tag if provided (for tracking in our scaling tests)
    if tag:
        print(f"Flow run with tag: {tag}")
    
    # Initial greeting
    greeting = say_hello(name)
    
    # Start data processing
    processed_data = data_processing(greeting)
    
    # Run enrichment and validation in parallel
    enriched_data = data_enrichment(processed_data)
    validation_result = data_validation(greeting)
    
    # Final processing that depends on both parallel tasks
    final_result = final_processing(enriched_data, validation_result)
    
    print(f"Flow execution completed with result: {final_result}")
    return final_result

if __name__ == "__main__":
    my_flow("from-github")
