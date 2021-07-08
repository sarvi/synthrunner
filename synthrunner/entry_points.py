"""
synthrunner.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the synthrunner module,
that are referenced in setup.py.
"""
import os
import logging
from synthrunner import utils

from dotenv import load_dotenv
import locust
import locust.clients
import locust.argument_parser
from locust.main import main as locust_main
from locust_plugins import *

from synthrunner import trace
import synthrunner.__version__ as version

log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name



def request(self, method, url, context={}, **kwargs):
    context['trace_data'] = trace.trace_start(method, url)
    rv = self._request(method, url, context=context, **kwargs)
    return rv


locust.clients.HttpSession._request = locust.clients.HttpSession.request
locust.clients.HttpSession.request = request

@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response,
                       context, exception, **kwargs):
    if exception:
        log.debug(f"Request to {name} failed with exception {exception}")
    else:
        log.debug(f"Successfully made a request to: {name}")
    status_code = 'ERROR' if exception else ('OK' if response.ok else 'ERROR')
    trace.trace_end(context['trace_data'], status_code)


@utils.timethis
def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        locust.__version__ = "%s(%s)"%(locust.__version__, version.__version__)
        locust.version = locust.__version__
        locust.argument_parser.version = locust.__version__
        load_dotenv()
        # Ensure that number of locust iterations is set, defaults to 1
        # Synthetic runner must not spawn new instances unless iterations > 1
        os.environ.setdefault('LOCUST_ITERATIONS', '1')
        # Synth runner always run in headless mode
        os.environ.setdefault('LOCUST_ONLY_SUMMARY', 'true')
        os.environ.setdefault('LOCUST_HEADLESS', 'true')
        os.environ.setdefault('LOCUST_USERS', '1')
        os.environ.setdefault('LOCUST_STOP_TIMEOUT', '60')
        os.environ.setdefault('LOCUST_TAGS', 'synthtest')
        locust_main()
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
