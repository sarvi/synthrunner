import os
import time
import subprocess as sp
from locust import HttpUser, task, between, tag


class WITHTTPUser(HttpUser):

    def on_start(self):
        self.volumes = []
        self.username = os.environ.get('WIT_USER', 'nobody')
        self.api_key = os.environ.get('WIT_APIKEY', '')
        self.client.headers = {"Authorization": "Token %s:%s" % (self.username, self.api_key)}

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


    @tag('synth')
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
                print("Volume created: %s" % spc_name)
                vol_data = response.json()
                self.volumes.append(vol_data['id'])
                vol_path = "%s/%s" % (vol_data['node']['cluster']['cluster_mount'],
                                      vol_data['junction_path'])
                process = sp.Popen('touch %s/test_wr' % vol_path, shell=True, stdout=sp.PIPE,
                                   stderr=sp.PIPE)
                output, error = process.communicate()
                if process.returncode == 0:
                    response.success()
                    process = sp.Popen('rm %s/test_wr' % vol_path, shell=True, stdout=sp.PIPE,
                                       stderr=sp.PIPE)
                    output, error = process.communicate()
                    self.del_volumes()
                else:
                    self.del_volumes()
                    response.failure("Space is not writable")
            else:
                self.del_volumes()
                response.failure(response.text)
