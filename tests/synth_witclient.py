import json
import time
import subprocess as sp
from locust import task, between, tag
from contrib.users import CLIUser


class WITCLIUser(CLIUser):
    wait_time = between(1, 2)
    spaces = []

    def teardown(self):
        for spc in self.spaces:
            process = sp.Popen('wit space list -space %s --json' % spc, shell=True, stdout=sp.PIPE,
                               stderr=sp.PIPE)
            output, error = process.communicate()
            if process.returncode == 0:
                output = output.decode('utf-8')
                results = json.loads(output)["cli_results"]
                for x in results:
                    vol_path = x['Storage Path']
                    del_process = sp.Popen('wit space delete -noprompt -path %s' % vol_path,
                                           shell=True, stdout=sp.PIPE,
                                           stderr=sp.PIPE)
                    output, error = del_process.communicate()
                    if del_process.returncode == 0:
                        print("Successfully deleted WIT space - " + spc)

    @task
    def wit_space_list(self, space=None, send_result=True):
        """ Test the wit space list command """
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

    @tag('synth')
    @task
    def wit_space_create(self):
        """ Test the wit space create command """
        command = "wit space create"
        space_name = "mytest_%d" % int(time.time())
        args = "-space %s -team wit --json" % space_name
        with self.client.execute(command, args, catch_response=True) as cli:
            if cli.failed == 0:
                self.spaces.append(space_name)
                list_failed = self.wit_space_list(space_name, send_result=False)
                if list_failed == 0:
                    cli.command = command
                    cli.success()
                else:
                    cli.command = command
                    cli.failure(list_failed, "WIT space not writable")
            else:
                cli.failure(cli.failed, cli.error.decode('utf-8'))
