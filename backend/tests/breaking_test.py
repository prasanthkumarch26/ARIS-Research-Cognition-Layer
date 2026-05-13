from locust import HttpUser, task, between, LoadTestShape
import time
import random

# Only cached topics — we want to stress the infrastructure, not arXiv
cached_topics = [
    "transformers", "BERT", "machine learning", "deep learning",
    "quantum computing", "biology", "physics", "mathematics",
    "neural networks", "computer vision"
]

class SearchUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(0.5, 1.5)  # More aggressive than before

    @task(1)
    def test_database_search(self):
        topic = random.choice(cached_topics)
        self.client.get(f"/search?query={topic}", name="/search")

    @task(3)
    def test_cached_search(self):
        topic = random.choice(cached_topics)
        self.client.get(f"/cache/search?query={topic}", name="/cache/search")


class StepLoadShape(LoadTestShape):
    """
    Automatically steps up users every 60 seconds.
    Watch the Locust graphs — when failures appear and latency spikes,
    that step is your breaking point.
    """
    step_duration = 360
    _start_time = None


    steps = [
        (200,  20),   # Baseline warmup
        (400,  25),   # Approaching limit
        (500,  25),   # Known good/bad boundary
        (600,  50),   # Expected p95 spike
        (750,  50),   # Confirm breaking point
        (1000, 100),  # Deep into overload territory
    ]


    def tick(self):
        # Track start time manually — compatible with Locust 2.x
        if self._start_time is None:
            self._start_time = time.time()

        run_time = time.time() - self._start_time

        for index, (users, spawn_rate) in enumerate(self.steps):
            if run_time < self.step_duration * (index + 1):
                return (users, spawn_rate)

        return None  # All steps done, test ends
