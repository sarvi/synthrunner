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

    def del_spaces(self):
        print("WITCLIUser: del_spaces")
        for spc in self.spaces:
            del_process = sp.Popen('wit space delete -noprompt -space %s' % spc,
                                    shell=True, stdout=sp.PIPE,
                                    stderr=sp.PIPE)
            output, error = del_process.communicate()
            if del_process.returncode == 0:
                print("Successfully deleted WIT space - " + spc)

    @task
    def wit_space_list(self, space=None, send_result=True):
        """ Test the wit space list command """
        print("WITCLIUser: space list")
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

    @tag('synthtest')
    @task
    def wit_space_create(self):
        """ Test the wit space create command """
        print("WITCLIUser: wit space create")
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
            self.del_spaces()