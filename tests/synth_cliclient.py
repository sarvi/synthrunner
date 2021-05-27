import time
from locust import User, task, between
from requests import Response

def on_execution(environment, identifier, response_length, start_time, response, context, err):
    environment.events.request.fire(
        request_type="EXEC",
        name=identifier,
        response_time=(time.monotonic() - start_time) * 1000,
        response_length=response_length,
        response=response,
        context=context,
        exception=err,
    )

class CLIResponse(Response):

    def __init__(self, out, err, rcode):
        self.output = out
        self.error = err
        self.status_code = rcode

    @property
    def ok(self):
        return self.status_code == 0

class CLIClient():
    """Run a command and capture its output string, error string and exit status"""

    def __init__(self, environment, headless=True):
        self.environment = environment
        self.headless = headless

    def execute(self, command, context={}, shell=True):
        start_time = time.monotonic()
        import subprocess as sp
        process = sp.Popen(command, shell = shell, stdout = sp.PIPE, stderr = sp.PIPE)
        self.pid = process.pid
        self.output, self.error = process.communicate()
        self.failed = process.returncode
        response_length = len(self.error + self.output)
        resp = CLIResponse(self.output, self.error, self.failed)
        on_execution(self.environment, command, response_length, start_time, resp, context, None)
        return self

    @property
    def returncode(self):
        return self.failed

class CLIUser(User):

    abstract = True

    def __init__(self, parent, headless=True):
        super().__init__(parent)
        self.headless = headless
        self.client = CLIClient(self.environment, headless)


class MyCLIUser(CLIUser):
    wait_time = between(1, 2)

    @task
    def hello_world_cli(self):
        self.client.execute("echo hello world")
