import simpy
import random
from system.queue_system_factory import QueueSystemFactory
from classes.analysis import Analysis
from classes.customer import Customer
from models.ros_model import ROSModel
from models.sjf_model import SJFModel
from models.dynamic_server import DynamicServerModel
from system.base_queue_system import BaseQueueSystem
from utils.customer_utils import select_customer_type


class BuffetSystem(BaseQueueSystem):
    """
    Hệ thống mô phỏng nhà hàng buffet với nhiều quầy thức ăn.
    
    Thuộc tính chính:
    - env: Môi trường SimPy quản lý thời gian và sự kiện
    - stations: Dictionary chứa tất cả các FoodStation
    - arrival_rates: Tốc độ khách đến từ mỗi cổng (λ0, λ1)
    - prob_matrices: Ma trận xác suất chọn quầy dựa trên cổng vào
    - analyzer: Đối tượng Analysis để ghi nhận số liệu
    """
    def __init__(self, env, station_configs, arrival_rates=(0.5,0.5), seed=None, policy='ROS', 
                 customer_type_distribution=None, customer_base_service=1.0,
                 probability_matrices=None, routing_mode='random', continue_probability=0.4):
        super().__init__(env, station_configs, seed=seed)
        self.rng = random.Random(seed)
        self.analyzer = Analysis()
        
        # Tạo các quầy thức ăn (FoodStation) từ cấu hình
        self.stations = {
            name: QueueSystemFactory.make_station(name, env, c=conf.get('c',1), K=conf.get('K',float('inf')), avg_service_time=conf.get('avg',1.0), rng=self.rng)
            for name, conf in station_configs.items()
        }
        
        self.arrival_rates = arrival_rates  # Tốc độ đến từ mỗi cổng
        self.customer_type_distribution = customer_type_distribution or {'normal': 1.0}
        self.customer_base_service = customer_base_service
        
        # Ma trận xác suất: {gate_id: {station_name: probability}}
        self.prob_matrices = probability_matrices or {}
        self.routing_mode = routing_mode  # 'random', 'shortest_wait', 'one_liner'
        self.continue_probability = continue_probability  # Xác suất tiếp tục đến quầy khác
        
        # Tạo danh sách thứ tự quầy cho chế độ one_liner
        self.station_order = list(station_configs.keys())
        
        # Chọn mô hình phục vụ dựa trên policy
        # Truyền reference đến buffet_system để models có thể gọi routing methods
        if policy == 'ROS':
            self.model = ROSModel(env, self.stations, self.analyzer, self.rng, 
                                prob_matrices=self.prob_matrices, routing_mode=self.routing_mode,
                                continue_probability=self.continue_probability, station_order=self.station_order,
                                buffet_system=self)
        elif policy == 'SJF':
            from config import STARVATION_THRESHOLD
            self.model = SJFModel(env, self.stations, self.analyzer, self.rng,
                                prob_matrices=self.prob_matrices, routing_mode=self.routing_mode,
                                continue_probability=self.continue_probability, station_order=self.station_order,
                                buffet_system=self, starvation_threshold=STARVATION_THRESHOLD)
        elif policy == 'DYNAMIC':
            self.model = DynamicServerModel(env, self.stations, self.analyzer, self.rng,
                                          prob_matrices=self.prob_matrices, routing_mode=self.routing_mode,
                                          continue_probability=self.continue_probability, station_order=self.station_order,
                                          buffet_system=self)
        else:
            raise ValueError('Unknown policy')
    
    def random_choose(self, customer):
        """
        Chọn quầy thức ăn ngẫu nhiên dựa trên ma trận xác suất.
        
        Args:
            customer: Đối tượng Customer
            
        Returns:
            str: Tên quầy được chọn, hoặc None nếu không có quầy nào khả dụng
        """
        gate = customer.arrival_gate
        
        # Lấy ma trận xác suất cho cổng này
        if gate in self.prob_matrices:
            probs = self.prob_matrices[gate]
        else:
            # Nếu không có ma trận, chọn ngẫu nhiên đều
            available = [s for s in self.stations.keys() if not customer.has_visited(s)]
            if not available:
                return None
            return self.rng.choice(available)
        
        # Lọc các quầy chưa được thăm (cho indulgent customers)
        available_stations = {s: p for s, p in probs.items() 
                            if s in self.stations and not customer.has_visited(s)}
        
        if not available_stations:
            return None
        
        # Chọn ngẫu nhiên dựa trên xác suất
        rand = self.rng.random()
        cumulative = 0.0
        total_prob = sum(available_stations.values())
        
        for station, prob in available_stations.items():
            cumulative += prob / total_prob
            if rand <= cumulative:
                return station
        
        return list(available_stations.keys())[-1]
    
    def shortest_expected_wait(self, customer):
        """
        Khách hàng quan sát các quầy và chọn quầy có ít người nhất.
        
        Args:
            customer: Đối tượng Customer
            
        Returns:
            str: Tên quầy có ít khách nhất, hoặc None
        """
        available = [s for s in self.stations.keys() 
                     if not customer.has_visited(s) and self.stations[s].can_enter()]
        
        if not available:
            return None
        
        # Chọn quầy có ít khách nhất trong hệ thống
        return min(available, key=lambda s: self.stations[s].customers_in_system())
    
    def one_liner(self, customer):
        """
        Khách hàng đi qua tất cả các quầy theo thứ tự định sẵn.
        Mỗi quầy chỉ được thăm một lần.
        
        Args:
            customer: Đối tượng Customer
            
        Returns:
            str: Quầy tiếp theo trong thứ tự, hoặc None nếu đã thăm hết
        """
        # Tìm quầy đầu tiên chưa được thăm
        for station_name in self.station_order:
            if not customer.has_visited(station_name):
                return station_name
        return None


    def run(self, until=100, util_time=None):
        # Support both parameter names for compatibility
        if util_time is not None:
            until = util_time
        self.env.process(self.generate_customers())
        self.env.run(until=until)
        self.analyzer.print_report()

    def generate_customers(self):
        total_rate = sum(self.arrival_rates)
        while True:
            ia = self.rng.expovariate(total_rate)
            yield self.env.timeout(ia)
            p = self.rng.random() * total_rate
            gate = 0 if p < self.arrival_rates[0] else 1
            # Select customer type based on distribution
            customer_type = select_customer_type(self.rng, self.customer_type_distribution)
            c = Customer(gate, self.env, customer_type=customer_type, base_service=self.customer_base_service)
            self.analyzer.record_arrival(c)
            # delegate to model
            self.model.serve_customer(c)