import json, time
import subprocess as sp
from locust import task, between
from tests.locust_extra import CLIUser

class WITCLIUser(CLIUser):
    wait_time = between(1, 2)

    @task
    def wit_space_list(self, space=None, send_result=True):
        command = "wit space list"
        if space:
            args = "-space %s --json" % space
        else:
            args = "--json"
        with self.client.execute(command, args, catch_response=True) as cli:
            stdout = cli.output.decode('utf-8')
            stderr = cli.error.decode('utf-8')
            if cli.failed:
                cli.failure(cli.failed, stderr)
                return cli.failed
            results = json.loads(stdout)['cli_results']
            for x in results:
                vol_path = x['Storage Path']
                process = sp.Popen('touch %s/test_wr' % vol_path, shell=True, stdout=sp.PIPE,
                                   stderr=sp.PIPE)
                output, error = process.communicate()
                if process.returncode == 0:
                    if send_result:
                        cli.success()
                    process = sp.Popen('rm %s/test_wr' % vol_path, shell=True, stdout=sp.PIPE,
                                       stderr=sp.PIPE)
                    output, error = process.communicate()
                else:
                    if send_result:
                        cli.failure(process.returncode, "WIT space not writable")
            return cli.failed


    @task
    def wit_space_create(self):
        command = "wit space create"
        space_name = "mytest_%s" % int(time.monotonic())
        args = "-space %s -team wit --json" % space_name
        with self.client.execute(command, args, catch_response=True) as cli:
            if cli.failed == 0:
                list_failed = self.wit_space_list(space_name, send_result=False)
                if list_failed == 0:
                    cli.command = command
                    cli.success()
                else:
                    cli.command = command
                    cli.failure(list_failed, "WIT space not writable")
            else:
                cli.failure(cli.failed, cli.error.decode('utf-8'))









