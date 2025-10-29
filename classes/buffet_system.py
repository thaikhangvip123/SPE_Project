import simpy
import random
from system.queue_system_factory import QueueSystemFactory
from classes.analysis import Analysis
from classes.customer import Customer
from models.ros_model import ROSModel
from models.sjf_model import SJFModel
from models.dynamic_server import DynamicServerModel


class BuffetSystem:
    def __init__(self, env, station_configs, arrival_rates=(0.5,0.5), seed=None, policy='ROS'):
        self.env = env
        self.rng = random.Random(seed)
        self.station_configs = station_configs
        self.analyzer = Analysis()
        self.stations = {
            name: QueueSystemFactory.make_station(name, env, c=conf.get('c',1), K=conf.get('K',float('inf')), avg_service_time=conf.get('avg',1.0), rng=self.rng)
            for name, conf in station_configs.items()
        }
        self.arrival_rates = arrival_rates
        if policy == 'ROS':
            self.model = ROSModel(env, self.stations, self.analyzer, self.rng)
        elif policy == 'SJF':
            self.model = SJFModel(env, self.stations, self.analyzer, self.rng)
        elif policy == 'DYNAMIC':
            self.model = DynamicServerModel(env, self.stations, self.analyzer, self.rng)
        else:
            raise ValueError('Unknown policy')


    def run(self, util_time=100):
        self.env.process(self.generate_customers())
        self.env.run(until=util_time)
        self.analyzer.print_report()

    def generate_customers(self):
        total_rate = sum(self.arrival_rates)
        while True:
            ia = self.rng.expovariate(total_rate)
            yield self.env.timeout(ia)
            p = self.rng.random() * total_rate
            gate = 0 if p < self.arrival_rates[0] else 1
            c = Customer(gate, self.env)
            self.analyzer.record_arrival(c)
            # delegate to model
            self.model.serve_customer(c)