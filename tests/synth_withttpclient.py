import os
import logging
import time
import subprocess
from urllib.parse import urlparse
from locust import HttpUser, task, tag

log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name


class WITHTTPUser(HttpUser):

    def on_start(self):
        self.volumes = []
        self.username = os.environ.get('WIT_USER', 'nobody')
        self.api_key = os.environ.get('WIT_APIKEY', self._read_token(self.host))
        self.client.headers = {"Authorization": "Token %s:%s" % (self.username, self.api_key)}

    @staticmethod
    def _read_token(host):
        wit_dotpath = os.path.expanduser('~/.wit')
        hostname = urlparse(host).hostname
        token_file = "authorization.token." + hostname
        try:
            with open(os.path.join(wit_dotpath, token_file), "r") as tokenf:
                token = tokenf.read()
                token = token.strip()
                return token
        except OSError as err:
            log.debug("Cannot find token: %s " % str(err))
            return ""

    def get_team(self, name):
        res = self.client.get("/api/wit/team/?group__name=%s" % name)
        if res.ok:
            data = res.json()
            if data["count"]:
                return data['results'][0]
        return None

    def del_volumes(self):
        for vol in self.volumes:
            self.client.delete('/api/wit/volume/%d' % vol)

    @tag('synthtest')
    @task
    def create_volume(self):
        team = self.get_team('wit')
        spc_name = "synth_test_%d" % (int(time.time()))
        vol_name = 'space_%s_%s' % (self.username, spc_name)
        data = {
            "teamid": team['id'],
            "volume_name": vol_name,
            "site": 'sjc',
            "junction_path": 'users/%s/%s' % (self.username, vol_name),
            "archiveonexpiry": False
        }
        with self.client.post('/api/wit/volume/', json=data, catch_response=True) as response:
            if response.ok:
                log.debug("Volume created: %s" % spc_name)
                vol_data = response.json()
                self.volumes.append(vol_data['id'])
                vol_path = "%s/%s" % (vol_data['node']['cluster']['cluster_mount'],
                                      vol_data['junction_path'])
                touch_cmd = 'touch %s/test_wr' % vol_path
                process = subprocess.run(touch_cmd.split(), capture_output=True)
                if process.returncode == 0:
                    response.success()
                    log.debug("Space is writable")
                    clean_cmd = 'rm %s/test_wr' % vol_path
                    subprocess.run(clean_cmd.split())
                    self.del_volumes()
                else:
                    self.del_volumes()
                    err_msg = "Space is not writable."
                    log.debug(err_msg)
                    log.debug("STDOUT: " + process.stdout.decode('utf-8'))
                    log.debug("STDERR: " + process.stderr.decode('utf-8'))
                    response.failure("Space is not writable")
            else:
                self.del_volumes()
                response.failure(response.text)
