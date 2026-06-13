from locust import HttpUser, task, between
import random


class AIAnalyzerUser(HttpUser):
    wait_time = between(0.5, 1.5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_ids = []
    
    @task(3)
    def create_load_test(self):
        with self.client.post(
            "/api/v1/analysis/load-test",
            data={"period_days": "7", "analysis_type": "full"},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                task_id = response.json().get("task_id")
                if task_id:
                    self.task_ids.append(task_id)
    
    @task(2)
    def check_status(self):
        if self.task_ids:
            task_id = random.choice(self.task_ids[-10:])
            self.client.get(f"/api/v1/analysis/load-test/{task_id}/status")
    
    @task(1)
    def get_result(self):
        if self.task_ids:
            task_id = random.choice(self.task_ids[-10:])
            self.client.get(
                f"/api/v1/analysis/load-test/{task_id}/result",
                catch_response=True,
            )
            