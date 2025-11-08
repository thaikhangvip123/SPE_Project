import itertools
import random

_id_counter = itertools.count()

class Customer:
    def __init__(self, arrival_gate, env, customer_type='normal', base_service=1.0):
        self.id = next(_id_counter)
        self.arrival_gate = arrival_gate  # Gate 0 or 1
        self.arrival_time = env.now  # Time when customer arrives
        self.customer_type = customer_type  # 'normal', 'impatient', 'indulgent', 'erratic'
        self.patience_time = self._init_patience(customer_type)  # Max wait time before leaving
        self.base_service = base_service  # Base service time
        self.serve_time = {}  # Dictionary: {station_name: service_time}
        self.visited_stations = set()  # Track which stations customer has visited
        self.wait_start_times = {}  # Track when customer started waiting at each station

    def _init_patience(self, t):
        if t == 'impatient':
            return random.uniform(0.5, 2.0)
        elif t == 'indulgent':
            return random.uniform(5.0, 10.0)
        else:
            return random.uniform(2.0, 5.0)

    def sample_service_time(self, station_name, rng, mean_service_time):
        """
        Sample service time for a station based on customer type.
        
        Args:
            station_name: Name of the station
            rng: Random number generator
            mean_service_time: Average service time for the station
            
        Returns:
            float: Service time (exponentially distributed, modified by customer type)
        """
        # Exponential distribution: st ~ exp(1/mean_service_time)
        st = rng.expovariate(1.0 / mean_service_time)
        
        # Modify based on customer type
        if self.customer_type == 'indulgent':
            st *= 2.0  # Indulgent customers take 2x longer
        elif self.customer_type == 'erratic':
            st += mean_service_time * 0.5  # Erratic customers add extra time
        
        # Store service time for this station
        self.serve_time[station_name] = st
        return st
    
    def has_visited(self, station_name):
        """Check if customer has already visited this station."""
        return station_name in self.visited_stations
    
    def mark_visited(self, station_name):
        """Mark a station as visited."""
        self.visited_stations.add(station_name)
    
    def get_wait_time(self, current_time):
        """Get total wait time so far."""
        return current_time - self.arrival_time

    def __repr__(self):
        return f"Customer(id={self.id}, gate={self.arrival_gate}, type={self.customer_type})"