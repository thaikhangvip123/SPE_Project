import itertools
import random

_id_counter = itertools.count()

class Customer:
    def __init__(self, arrival_gate, env, customer_type='normal', base_service=1.0):
        self.id = next(_id_counter)
        self.arrival_gate = arrival_gate
        self.arrival_time = env.now
        self.customer_type = customer_type
        self.patience_time = self._init_patience(customer_type)
        self.base_service = base_service
        self.serve_time = {}

    def _init_patience(self, t):
        if t == 'impatient':
            return random.uniform(0.5, 2.0)
        elif t == 'indulgent':
            return random.uniform(5.0, 10.0)
        else:
            return random.uniform(2.0, 5.0)

    def sample_service_time(self, station_name, rng, mean_service_time):
        st = rng.expovariate(1.0 / mean_service_time)
        if self.customer_type == 'indulgent':
            st *= 2.0
        elif self.customer_type == 'erratic':
            st += mean_service_time * 0.5
        self.serve_time[station_name] = st
        return st

    def __repr__(self):
        return f"Customer(id={self.id}, gate={self.arrival_gate}, type={self.customer_type})"