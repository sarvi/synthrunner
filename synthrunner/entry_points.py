"""
synthrunner.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the synthrunner module,
that are referenced in setup.py.
"""

from sys import argv

import gevent
from locust import HttpUser, task, between
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging

setup_logging("INFO", None)


class User(HttpUser):
    wait_time = between(1, 3)
    host = "https://docs.locust.io"

    @task
    def my_task(self):
        self.client.get("/")

    @task
    def task_404(self):
        self.client.get("/non-existing-path")


def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:

        # setup Environment and Runner
        env = Environment(user_classes=[User])
        env.create_local_runner()

        # start a WebUI instance
        # env.create_web_ui("127.0.0.1", 8089)

        # start a greenlet that periodically outputs the current stats
        gevent.spawn(stats_printer(env.stats))

        # start a greenlet that save current stats to history
        gevent.spawn(stats_history, env.runner)

        # start the test
        env.runner.start(1, spawn_rate=10)

        # in 10 seconds stop the runner
        gevent.spawn_later(10, lambda: env.runner.quit())

        # wait for the greenlets
        env.runner.greenlet.join()

        # stop the web server for good measures
        # env.web_ui.stop()
        # user_cmd = argv[1]
        # if user_cmd == 'install':
        #     print('install subcommand')
        # else:
        #     RuntimeError('please supply a command for synthrunner - e.g. install.')  # noqa: E501
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
