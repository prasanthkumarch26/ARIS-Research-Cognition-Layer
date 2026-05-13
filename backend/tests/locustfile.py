from locust import HttpUser, task, between
import random

topics = ["transformers", "BERT", "ResNet", "GPT", "diffusion models", "quantum computing", "machine learning", "deep learning", "biology", "chemistry", "physics", "mathematics", "neural networks", "computer vision"]
# new_topics = [
#     "cryogenic electron microscopy protein folding",
#     "stochastic gradient descent convergence proofs",
#     "zebrafish neuronal circuit mapping",
#     "topological quantum error correction",
#     "paleoclimate ice core isotope analysis",
#     "Byzantine fault tolerant consensus algorithms",
#     "synthetic aperture radar interferometry",
#     "optogenetic control of dopamine neurons",
# ]

class SearchUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(1, 3)

    @task(1)
    def test_database_search(self):
        self.client.get(f"/search?query={random.choice(topics)}", name="/search")

    @task(3)
    def test_cached_search(self):
        self.client.get(f"/cache/search?query={random.choice(topics)}", name="/cache/search")
