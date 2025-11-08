import simpy
import random
from system.base_queue_system import BaseQueueSystem
from system.queue_system_factory import QueueSystemFactory
from classes.analysis import Analysis
from classes.customer import Customer
from models.ros_model import ROSModel
from utils.customer_utils import select_customer_type


class MultiQueueSystem(BaseQueueSystem):
    """System where each station behaves like an independent queue (own arrival stream).


    This class launches one arrival generator per station by default.
    """
    def __init__(self, env, station_configs, arrival_rates=None, seed=None, policy='ROS',
                 customer_type_distribution=None, customer_base_service=1.0):
        super().__init__(env, station_configs, seed=seed)
        self.rng = random.Random(seed)
        self.analyzer = Analysis()
        self.customer_type_distribution = customer_type_distribution or {'normal': 1.0}
        self.customer_base_service = customer_base_service
        self.stations = {
        name: QueueSystemFactory.make_station(name, env, c=conf.get('c',1), K=conf.get('K',float('inf')), avg_service_time=conf.get('avg',1.0), rng=self.rng)
        for name, conf in station_configs.items()
        }
        # Convert tuple arrival_rates to dict if needed
        if isinstance(arrival_rates, (tuple, list)):
            # If tuple/list, distribute rates to stations
            station_names = list(station_configs.keys())
            if len(arrival_rates) == len(station_names):
                self.arrival_rates = {name: rate for name, rate in zip(station_names, arrival_rates)}
            else:
                # If mismatch, use equal distribution
                total_rate = sum(arrival_rates) if arrival_rates else 1.0
                rate_per_station = total_rate / len(station_names) if station_names else 0.5
                self.arrival_rates = {name: rate_per_station for name in station_names}
        else:
            self.arrival_rates = arrival_rates or {name: 0.5 for name in self.stations}
        
        # select model
        if policy == 'ROS':
            self.model = ROSModel(env, self.stations, self.analyzer, self.rng)
        elif policy == 'SJF':
            from models.sjf_model import SJFModel
            self.model = SJFModel(env, self.stations, self.analyzer, self.rng)
        elif policy == 'DYNAMIC':
            from models.dynamic_server import DynamicServerModel
            self.model = DynamicServerModel(env, self.stations, self.analyzer, self.rng)
        else:
            raise ValueError(f'Unknown policy: {policy}')

    def run(self, until=100, util_time=None):
        # Support both parameter names for compatibility
        if util_time is not None:
            until = util_time
        # start generator per station
        for name in self.stations:
            self.env.process(self._gen_for_station(name))
        self.env.run(until=until)
        self.analyzer.print_report()
    
    def generate_customers(self):
        """Generate customers for each station (abstract method implementation)."""
        for name in self.stations:
            self.env.process(self._gen_for_station(name))

    def _gen_for_station(self, station_name):
        rate = self.arrival_rates.get(station_name, 0.5)
        while True:
            ia = self.rng.expovariate(rate)
            yield self.env.timeout(ia)
            # Select customer type based on distribution
            customer_type = select_customer_type(self.rng, self.customer_type_distribution)
            c = Customer(arrival_gate=0, env=self.env, customer_type=customer_type, 
                        base_service=self.customer_base_service)
            self.analyzer.record_arrival(c)
            # route customer to the station's model
            self.model.serve_customer(c)