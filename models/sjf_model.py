from .base_model import BaseModel


class SJFModel(BaseModel):
    def serve_customer(self, customer):
        def proc():
            # choose smallest avg_service_time station
            name = min(self.stations.keys(), key=lambda k: self.stations[k].avg_service_time)
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