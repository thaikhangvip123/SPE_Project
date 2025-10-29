import simpy
import random

class FoodStation:
    def __init__(self, name, env, c=1, K=float('inf'), avg_service_time=1.0, rng=None):
        self.name = name
        self.env = env
        self.c = c
        self.capacity_K = K
        self.avg_service_time = avg_service_time
        self.resource = simpy.Resource(env, capacity=c)
        self.rng = rng or random

    def customers_in_system(self):
        return self.resource.count + len(self.resource.queue)

    def can_enter(self):
        return self.customers_in_system() < self.capacity_K

    def request_service(self, customer):
        return self.env.process(self._serve(customer))

    def _serve(self, customer):
        if not self.can_enter():
            return False
        arrive = self.env.now
        with self.resource.request() as req:
            patience = customer.patience_time
            results = yield req | self.env.timeout(patience)
            if req not in results:
                return False
            wait = self.env.now - arrive
            service_time = customer.sample_service_time(self.name, self.rng, self.avg_service_time)
            yield self.env.timeout(service_time)
            return wait, service_time