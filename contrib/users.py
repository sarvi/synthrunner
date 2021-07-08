import time
import subprocess as sp
from requests import Response
from locust import User
from synthrunner import trace


class CLIResponse(Response):

    def __init__(self, out, err, rcode):
        super().__init__()
        self.output = out
        self.error = err
        self.status_code = rcode

    @property
    def ok(self):
        return self.status_code == 0


class CLIClient:
    """Run a command and capture its output string, error string and exit status"""

    def __init__(self, environment, headless=True, catch_response=False):
        self.environment = environment
        self.headless = headless
        self.pid = None
        self.output = None
        self.error = None
        self.failed = False
        self.command = None
        self.args = None
        self.catch_response = catch_response
        self.start_time = None

    @staticmethod
    def _on_execution(environment, identifier, response_length, start_time, response, context, err):
        environment.events.request.fire(
            request_type="EXEC",
            name=identifier,
            response_time=(time.monotonic() - start_time) * 1000,
            response_length=response_length,
            response=response,
            context=context,
            exception=err,
        )

    def execute(self, command, args=None, context=None, shell=True, catch_response=False):
        if context is None:
            context = {}
        context['trace_data'] = trace.trace_start("EXEC", command)
        self.start_time = time.monotonic()
        self.command = command
        self.args = args
        self.catch_response = catch_response
        process = sp.Popen(command + ' ' + args, shell=shell, stdout=sp.PIPE, stderr=sp.PIPE)
        self.pid = process.pid
        self.output, self.error = process.communicate()
        self.failed = process.returncode
        response_length = len(self.error + self.output)
        resp = CLIResponse(self.output, self.error, self.failed)
        self.context = context
        if not self.catch_response:
            self._on_execution(self.environment, command, response_length, self.start_time, resp, context, None)
        return self

    def success(self):
        self.failed = 0
        response_length = len(self.error + self.output)
        resp = CLIResponse(self.output, self.error, 0)
        self._on_execution(self.environment, self.command, response_length, self.start_time, resp, self.context, None)

    def failure(self, rcode, err_msg):
        self.failed = rcode
        response_length = len(self.error + self.output)
        resp = CLIResponse(self.output, err_msg, self.failed)
        self._on_execution(self.environment, self.command, response_length, self.start_time, resp, self.context, None)


    @property
    def returncode(self):
        return self.failed

    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        return


class CLIUser(User):

    abstract = True

    def __init__(self, parent, headless=True):
        super().__init__(parent)
        self.headless = headless
        self.client = CLIClient(self.environment, headless)
