from abc import ABC, abstractmethod


class BaseModel(ABC):
    def __init__(self, env, stations, analyzer, rng):
        self.env = env
        self.stations = stations
        self.analyzer = analyzer
        self.rng = rng


    @abstractmethod
    def serve_customer(self, customer):
        pass


# ===================== FILE: models/ros_model.py =====================
from .base_model import BaseModel


class ROSModel(BaseModel):
    def serve_customer(self, customer):
        def proc():
            while True:
                name = self.rng.choice(list(self.stations.keys()))
                station = self.stations[name]
                res = yield station.request_service(customer)
                if not res:
                    self.analyzer.record_blocked(customer, self.env.now)
                    break
                wait, service_time = res
                self.analyzer.record_wait(customer, wait)
                self.analyzer.record_service(customer, service_time)
                if self.rng.random() < 0.4:
                    continue
                self.analyzer.record_departure(customer, self.env.now)
                break
        return self.env.process(proc())