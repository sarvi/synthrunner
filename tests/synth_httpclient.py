from locust import HttpUser, task, between, tag

# class MyUser(User):
#     @task
#     def my_task(self):
#         print("executing my_task")

#     wait_time = between(0.5, 10)


class QuickstartUser(HttpUser):
    wait_time = between(1, 2)

    @tag('synthtest')
    @task
    def hello_world(self):
        self.client.get("/")


    # def on_start(self):
    #     self.client.post("/login", json={"username": "foo", "password": "bar"})
