import simpy
from typing import Dict
from system.queue_system_factory import create_queue
from system.validation_analyzer import ValidationAnalyzer

class MultiQueueSystem:
    def __init__(self, env, config):
        self.env = env
        self.config = config
        self.stations: Dict[str, BaseQueueSystem] = {}
        self.validators = []

        self.global_pool = None
        if config.get("dynamic_shared"):
            self.global_pool = simpy.Resource(env, capacity=config["total_servers"])

        for name, cfg in config["stations"].items():
            servers = self.global_pool if cfg["discipline"] == "DYNAMIC" else simpy.Resource(env, capacity=cfg["c"])
            extra = {"all_stations": self.stations} if cfg["discipline"] == "DYNAMIC" else {}
            q = create_queue(
                discipline=cfg["discipline"],
                env=env,
                servers=servers,
                avg_service_rate=1 / cfg["service_time"],
                capacity_K=cfg.get("K"),
                **extra
            )
            self.stations[name] = q
            q.start()

    def generate_arrivals(self, gate: int):
        lambda_ = self.config["arrival_rates"][gate]
        matrix = self.config["prob_matrices"][gate]
        while True:
            yield self.env.timeout(random.expovariate(lambda_))
            cust_type = random.choices(list(self.config["customer_types"].keys()), weights=list(self.config["customer_types"].values()))[0]
            serve_time = 1.0  # Base, adjust by type
            if cust_type == "indulgent":
                serve_time *= 2
            # Add other type adjustments
            cust = Customer(self.env, self.env.now, serve_time, gate, matrix, cust_type)
            self.env.process(self.route_customer(cust))

    def route_customer(self, cust: 'Customer'):
        visited = set()
        while True:
            station = cust.choose_station(self.stations.keys(), visited)
            if station is None:
                break
            visited.add(station)
            self.stations[station].arrive(cust)
            # Wait for service to complete (since serve is in background)
            yield self.env.timeout(0)  # Placeholder, actual service is async

        self.config["analysis"].record_exit(self.env.now, cust)

    def run(self, until: float):
        for g in (0, 1):
            self.env.process(self.generate_arrivals(g))
        self.env.run(until=until)

        for name, q in self.stations.items():
            cfg = self.config["stations"][name]
            v = ValidationAnalyzer(q, sum(self.config["arrival_rates"]), 1/cfg["service_time"], cfg["c"], cfg.get("K"))
            self.validators.append(v)
            v.report()