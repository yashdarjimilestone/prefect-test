# flows/my_flow.py
from prefect import flow, task

@task
def say_hello(name: str):
    print(f"hello, {name}!")

@flow(log_prints=True)
def my_flow(name: str = "world"):
    say_hello(name)

if __name__ == "__main__":
    my_flow("from-github")
