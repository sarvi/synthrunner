import logging
import time
import subprocess
from requests import Response
from locust import User
from locust.exception import CatchResponseError, ResponseError
from synthrunner import trace

log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name


class CLIResponse(Response):

    def __init__(self, out, err, rcode):
        super().__init__()
        self.output = out
        self.error = err
        self.status_code = rcode

    @property
    def ok(self):
        return self.status_code == 0

    def raise_for_status(self):
        if hasattr(self, "error") and self.error:
            raise self.error
        Response.raise_for_status(self)


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

    def execute(self, command, args=None, context=None, catch_response=False, shell=False, ):
        if context is None:
            context = {}
        context['trace_data'] = trace.trace_start(
            "EXEC",
            command if isinstance(command, list) else [i.strip() for i in command.split()],
            getattr(self, 'instancename', None))
        self.start_time = time.monotonic()
        self.command = ' '.join(command) if isinstance(command, list) else command
        self.args = args if isinstance(args, list) else [i.strip() for i in args.split(args)]
        self.catch_response = catch_response
        self.exc = None
        if shell:
            if isinstance(command, list):
                command = ' '.join(command)
            if isinstance(args, list):
                args = ' '.join(args)
            cmd_line = command + ' ' + args
        else:
            if isinstance(command, list) == isinstance(args, list):
                cmd_line = (command+args)
            else:
                cmd_line = (command.split()+args) if isinstance(args, list) else (' '.join(command) + ' ' + args)
        process = subprocess.run(cmd_line, capture_output=True, shell=shell)
        self.failed = process.returncode
        self.output = process.stdout.decode('utf-8')
        self.error = process.stderr.decode('utf-8')
        log.debug("Command line: {}".format(cmd_line))
        log.debug("STDOUT: " + self.output)
        log.debug("STDERR: " + self.error)
        response_length = len(self.error + self.output)
        resp = CLIResponse(self.output, self.error, self.failed)
        self.context = context
        if not self.catch_response:
            if self.failed != 0:
                self.exc = ResponseError(self.error)
            self._on_execution(self.environment, self.command, response_length, self.start_time, resp, context, self.exc)
        return self

    def success(self):
        self.failed = 0
        response_length = len(self.error + self.output)
        resp = CLIResponse(self.output, self.error, 0)
        if self.catch_response:
            self._on_execution(self.environment, self.command, response_length, self.start_time, resp, self.context, None)

    def failure(self, rcode, err_msg):
        self.failed = rcode
        response_length = len(self.error + self.output)
        resp = CLIResponse(self.output, err_msg, self.failed)
        if self.catch_response:
            if err_msg:
                self.exc = CatchResponseError(err_msg)
            self._on_execution(self.environment, self.command, response_length, self.start_time, resp, self.context, self.exc)

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
