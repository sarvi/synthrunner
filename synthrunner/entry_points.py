"""
synthrunner.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the synthrunner module,
that are referenced in setup.py.
"""
from functools import wraps
import logging
import configargparse
from locust import events
from locust.exception import StopUser
from locust.env import Environment
from locust.runners import Runner
from locust import TaskSet
from locust.user.task import DefaultTaskSet
import locust.main

@events.init_command_line_parser.add_listener
def add_checks_arguments(parser: configargparse.ArgumentParser):
    other = parser.add_argument_group(
        "locust-plugins - Extras",
    )
    # fix for https://github.com/locustio/locust/issues/1085
    other.add_argument(
        "-i",
        "--iterations",
        type=int,
        help="Dont run more than this number of task iterations and terminate once they have finished",
        env_var="LOCUST_ITERATIONS",
        default=0,
    )
    other.add_argument(
        "--console-stats-interval",
        type=int,
        help="Interval at which to print locust stats to command line",
        env_var="LOCUST_CONSOLE_STATS_INTERVAL",
        default=locust.stats.CONSOLE_STATS_INTERVAL_SEC,
    )


@events.test_start.add_listener
def set_up_iteration_limit(environment: Environment, **_kwargs):
    options = environment.parsed_options
    locust.stats.CONSOLE_STATS_INTERVAL_SEC = environment.parsed_options.console_stats_interval
    if options.iterations:
        runner: Runner = environment.runner
        runner.iterations_started = 0
        runner.iteration_target_reached = False

        def iteration_limit_wrapper(method):
            @wraps(method)
            def wrapped(self, task):
                if runner.iterations_started == options.iterations:
                    if not runner.iteration_target_reached:
                        runner.iteration_target_reached = True
                        logging.info(
                            f"Iteration limit reached ({options.iterations}), stopping Users at the start of their next task run"
                        )
                    if runner.user_count == 1:
                        logging.info("Last user stopped, quitting runner")
                        runner.quit()
                    raise StopUser()
                runner.iterations_started = runner.iterations_started + 1
                method(self, task)

            return wrapped

        # monkey patch TaskSets to add support for iterations limit. Not ugly at all :)
        TaskSet.execute_task = iteration_limit_wrapper(TaskSet.execute_task)
        DefaultTaskSet.execute_task = iteration_limit_wrapper(DefaultTaskSet.execute_task)



def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        locust.main.main()
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
