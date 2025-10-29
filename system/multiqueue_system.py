import simpy
import random
from base_queue_system import BaseQueueSystem
from factory import QueueSystemFactory
from analysis import Analysis
from customer import Customer
from models.ros_model import ROSModel


class MultiQueueSystem(BaseQueueSystem):
    """System where each station behaves like an independent queue (own arrival stream).


    This class launches one arrival generator per station by default.
    """
    def __init__(self, env, station_configs, arrival_rates=None, seed=None, policy='ROS'):
        super().__init__(env, station_configs, seed=seed)
        self.rng = random.Random(seed)
        self.analyzer = Analysis()
        self.stations = {
        name: QueueSystemFactory.make_station(name, env, c=conf.get('c',1), K=conf.get('K',float('inf')), avg_service_time=conf.get('avg',1.0), rng=self.rng)
        for name, conf in station_configs.items()
        }
        self.arrival_rates = arrival_rates or {name:0.5 for name in self.stations}
        # select model
        if policy == 'ROS':
            self.model = ROSModel(env, self.stations, self.analyzer, self.rng)
        else:
            from models.base_model import BaseModel
            self.model = ROSModel(env, self.stations, self.analyzer, self.rng)

    def run(self, until=100):
        # start generator per station
        for name in self.stations:
            self.env.process(self._gen_for_station(name))
        self.env.run(until=until)
        self.analyzer.print_report()

    def _gen_for_station(self, station_name):
        rate = self.arrival_rates.get(station_name, 0.5)
        while True:
            ia = self.rng.expovariate(rate)
            yield self.env.timeout(ia)
            c = Customer(arrival_gate=0, env=self.env)
            self.analyzer.record_arrival(c)
            # route customer to the station's model
            self.model.serve_customer(c)