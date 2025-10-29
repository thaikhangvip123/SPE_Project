from .base_model import BaseModel


class DynamicServerModel(BaseModel):
    """Simple dynamic allocation: pick least-loaded station by customers_in_system()."""
    def serve_customer(self, customer):
        def proc():
            name = min(self.stations.keys(), key=lambda k: self.stations[k].customers_in_system())
            station = self.stations[name]
            res = yield station.request_service(customer)
            if not res:
                self.analyzer.record_blocked(customer, self.env.now)
                return
            wait, service_time = res
            self.analyzer.record_wait(customer, wait)
            self.analyzer.record_service(customer, service_time)
            self.analyzer.record_departure(customer, self.env.now)
        return self.env.process(proc())