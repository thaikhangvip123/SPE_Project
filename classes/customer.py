import random
from typing import List, Dict

class Customer:
    _counter = 0

    def __init__(self, env, arrival_time, serve_time, arrival_gate, prob_matrix, customer_type, patience_time=None):
        Customer._counter += 1
        self.id = Customer._counter
        self.env = env
        self.arrival_time = arrival_time
        self.serve_time = serve_time
        self.arrival_gate = arrival_gate
        self.prob_matrix = prob_matrix
        self.customer_type = customer_type
        self.patience = patience_time or float('inf')

    def choose_station(self, stations: List[str], visited: set) -> str or None:
        # Simplify: use probabilities to choose next station or exit
        probs = self.prob_matrix[0]  # Example, use actual logic from report
        choices = list(stations) + ["exit"]
        choice = random.choices(choices, weights=probs)[0]
        if choice == "exit" or choice in visited:
            return None
        return choice