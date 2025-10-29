from abc import ABC, abstractmethod
from typing import List
import simpy
import random

class BaseQueueSystem(ABC):
    def __init__(self, env: simpy.Environment, servers: simpy.Resource,
                 avg_service_rate: float, capacity_K: int = None):
        self.env = env
        self.servers = servers
        self.mu = avg_service_rate
        self.K = capacity_K
        self.waiting: List['Customer'] = []
        self.wait_times = []
        self.service_times = []
        self.blocked = 0
        self.reneged = 0

    @abstractmethod
    def _select_next(self) -> 'Customer':
        pass

    def arrive(self, cust: 'Customer'):
        if self.K is not None and len(self.waiting) >= self.K:
            self.blocked += 1
            return False
        self.waiting.append(cust)
        cust.arrival_time = self.env.now  # Update to station arrival
        return True

    def _serve_one(self):
        while True:
            if not self.waiting:
                yield self.env.timeout(0)
                continue

            cust = self._select_next()
            self.waiting.remove(cust)

            req = self.servers.request()
            yield req

            self.wait_times.append(self.env.now - cust.arrival_time)

            service_t = random.expovariate(self.mu) * cust.serve_time
            yield self.env.timeout(service_t)
            self.service_times.append(service_t)

            self.servers.release(req)

    def start(self):
        self.env.process(self._serve_one())