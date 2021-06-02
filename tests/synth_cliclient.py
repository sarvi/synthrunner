import time
from locust import task, between
from tests.locust_extra import CLIUser

class MyCLIUser(CLIUser):
    wait_time = between(1, 2)

    @task
    def hello_world_cli(self):
        cli = self.client.execute("echo", "hello world")
