from locust import task, between, tag
from contrib.users import CLIUser


class MyCLIUser(CLIUser):
    wait_time = between(1, 2)

    @tag('synth')
    @task
    def hello_world_cli(self):
        self.client.execute("echo", "hello world")
