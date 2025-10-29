from abc import ABC, abstractmethod


class BaseQueueSystem(ABC):
    """Abstract base class for queue systems (single or multi-line).


    Responsibilities:
    - hold env and station configs
    - define run() and customer generation contract
    """
    def __init__(self, env, station_configs, seed=None):
        self.env = env
        self.station_configs = station_configs
        self.seed = seed


    @abstractmethod
    def run(self, until):
        pass


    @abstractmethod
    def generate_customers(self):
        pass