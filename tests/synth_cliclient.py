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


    # @task
    # def wit_space_list(self, space=None, send_result=True):
    #     """ Test the wit space list command """
    #     print("WITCLIUser: space list")
    #     command = "wit space list"
    #     args = "-h" % space
    #     with self.client.execute(command, args, catch_response=True) as cli:
    #         stdout = cli.output.decode('utf-8')
    #         stderr = cli.error.decode('utf-8')
    #         if cli.failed:
    #             cli.failure(cli.failed, stderr)
    #             return cli.failed
    #         return cli.failed

    @tag('synthtest')
    @task
    def wit_space_create(self):
        """ Test the wit space create command """
        print("WITCLIUser: wit space create")
        command = "wit space create"
        args = "-h"
        with self.client.execute(command, args, catch_response=True) as cli:
            if cli.failed == 0:
                cli.success()
            else:
                cli.failure(cli.failed, cli.error)
