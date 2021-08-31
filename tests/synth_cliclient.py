import json
import time
import subprocess as sp
from locust import task, between, tag
from contrib.users import CLIUser


class WITCLIUser(CLIUser):
    wait_time = between(1, 2)

    def on_start(self):
        print("WITCLIUser: on_start")
        self.spaces = []

    def on_stop(self):
        print("WITCLIUser: on_stop")
        self.spaces = []


    @tag('synthtest')
    @task
    def helloworldtest(self):
        """ Test the wit space create command """
        print("A simple test")
        with self.client.execute(['ls'], ['/var'], catch_response=True) as cli:
            if cli.failed == 0:
                if 'log' not in cli.output.splitlines():
                    cli.failure(1, "Var does not have log directory")
                else:
                    cli.success()
            else:
                cli.failure(cli.failed, cli.error+"Var does not have log directory")
