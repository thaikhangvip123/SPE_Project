import statistics


class Analysis:
    def __init__(self):
        self.arrivals = 0
        self.departures = 0
        self.blocked = 0
        self.wait_times = []
        self.service_times = []

    def record_arrival(self, customer):
        self.arrivals += 1

    def record_blocked(self, customer, when):
        self.blocked += 1

    def record_wait(self, customer, wait):
        self.wait_times.append(wait)

    def record_service(self, customer, service_time):
        self.service_times.append(service_time)


    def record_departure(self, customer, when):
        self.departures += 1


    def calculate_statistics(self):
        stats = {}
        stats['arrivals'] = self.arrivals
        stats['departures'] = self.departures
        stats['blocked'] = self.blocked
        stats['avg_wait'] = statistics.mean(self.wait_times) if self.wait_times else 0.0
        stats['avg_service'] = statistics.mean(self.service_times) if self.service_times else 0.0
        stats['std_wait'] = statistics.pstdev(self.wait_times) if self.wait_times else 0.0
        return stats


    def print_report(self):
        s = self.calculate_statistics()
        print('--- Simulation Report ---')
        print(f"Arrivals: {s['arrivals']}")
        print(f"Departures: {s['departures']}")
        print(f"Blocked (rejected due to K): {s['blocked']}")
        print(f"Average wait time: {s['avg_wait']:.4f}")
        print(f"Average service time: {s['avg_service']:.4f}")