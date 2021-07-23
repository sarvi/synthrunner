import os
from os import environ
import re
import getpass
import json
import logging
import time
import subprocess
from locust import task, between, tag
from contrib.users import CLIUser

log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name

SITE=environ.get('SITE') or "UNKNOWN"
USERNAME=getpass.getuser()

class WITCLIUser(CLIUser):
    wait_time = between(1, 2)

    def on_start(self):
        print("WITCLIUser: on_start")
        self.del_spaces()
        self.spaces = []

    def on_stop(self):
        print("WITCLIUser: on_stop")
        self.del_spaces()
        self.spaces = []

    def del_spaces(self):
        print("WITCLIUser: del_spaces")
        proc = subprocess.run(['wit', 'space', 'list','-team', 'wit', '--json'], capture_output=True)
        if proc.returncode != 0:
            os.exit(1)
        spaces = json.loads(proc.stdout.decode('utf-8'))['cli_results']

        for spc in spaces:
            spc = spc['Space Name']
            if not f'space_{USERNAME}_synthetictest_{SITE}' == spc:
                continue
            log.debug(f"Clearning up workspace {spc}")
            proc = subprocess.run(['wit', 'space', 'delete', '-noprompt', '-space', spc], capture_output=True)
            if proc.returncode == 0:
                log.debug("Successfully deleted WIT space - " + spc)
            else:
                log.error("Failed to delete space {}\nSTDOUT: {}\STDERR: {}".format(
                    spc, proc.stdout.decode('utf-8'), proc.stderr.decode('utf-8')))

    @tag('synthtest')
    @task
    def wit_space_test(self):
        """ Test the wit space create command """
        command = "wit space create"
        spacename = f"synthetictest_{SITE}"
        log.debug(f"WITCLIUser: wit space create {spacename}")
        with self.client.execute(['wit', 'space', 'create'], ['-space', spacename, '-noprompt', '-json', '-team', 'wit'], catch_response=True) as cli:
            if cli.failed == 0:
                spacename = f'space_{USERNAME}_{spacename}'
                self.spaces.append(spacename)
                cli.success()
            else:
                cli.failure(cli.failed, cli.error)
                return
        log.debug(f"WITCLIUser: wit space list -space {spacename}")
        with self.client.execute(['wit', 'space', 'list'], ['-space', spacename, '-noprompt', '-json'], catch_response=True) as cli:
            if cli.failed == 0:
                results = json.loads(cli.output)['cli_results']
                if len(results) != 1:
                    cli.failure(1, f"'wit space list -space {spacename}' should have returned 1 space")
                    return
                spacepath = results[0]['Storage Path']
                if not os.access(spacepath, os.W_OK):
                    cli.failure(1, f"Workspace path: {spacepath} not writeable")
                    return
                cli.success()
            else:
                cli.failure(cli.failed, cli.error)
                return

        log.debug(f"WITCLIUser: wit space delete -space {spacename}")
        with self.client.execute(['wit', 'space', 'delete'], ['-space', spacename, '-noprompt'], catch_response=True) as cli:
            if cli.failed == 0:
                cli.success()
            else:
                cli.failure(cli.failed, cli.error)
