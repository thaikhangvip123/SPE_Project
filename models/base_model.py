from abc import ABC, abstractmethod


class BaseModel(ABC):
    """
    Lớp cơ sở trừu tượng cho tất cả các mô hình phục vụ.
    
    Các mô hình con sẽ triển khai logic phục vụ khách hàng khác nhau:
    - ROS: Random Order Serving
    - SJF: Shortest Job First (với starvation prevention)
    - Dynamic Server: Phân bổ server động
    """
    def __init__(self, env, stations, analyzer, rng, 
                 prob_matrices=None, routing_mode='random', 
                 continue_probability=0.4, station_order=None, buffet_system=None):
        self.env = env  # Môi trường SimPy
        self.stations = stations  # Dictionary các FoodStation
        self.analyzer = analyzer  # Đối tượng Analysis để ghi số liệu
        self.rng = rng  # Random number generator
        self.prob_matrices = prob_matrices or {}  # Ma trận xác suất
        self.routing_mode = routing_mode  # Chế độ routing
        self.continue_probability = continue_probability  # Xác suất tiếp tục
        self.station_order = station_order or []  # Thứ tự quầy cho one_liner
        self.buffet_system = buffet_system  # Reference đến BuffetSystem để gọi routing methods

    @abstractmethod
    def serve_customer(self, customer):
        """
        Phục vụ một khách hàng theo logic của mô hình cụ thể.
        
        Args:
            customer: Đối tượng Customer cần được phục vụ
        """
        pass
    
    def select_station(self, customer):
        """
        Chọn quầy thức ăn dựa trên routing_mode.
        
        Args:
            customer: Đối tượng Customer
            
        Returns:
            str: Tên quầy được chọn, hoặc None
        """
        if not self.buffet_system:
            # Fallback: chọn ngẫu nhiên nếu không có buffet_system
            available = [s for s in self.stations.keys() if not customer.has_visited(s)]
            return self.rng.choice(available) if available else None
        
        if self.routing_mode == 'one_liner':
            return self.buffet_system.one_liner(customer)
        elif self.routing_mode == 'shortest_wait':
            return self.buffet_system.shortest_expected_wait(customer)
        else:  # 'random' or default
            return self.buffet_system.random_choose(customer)


# ===================== FILE: models/ros_model.py =====================
from .base_model import BaseModel


class ROSModel(BaseModel):
    def serve_customer(self, customer):
        def proc():
            while True:
                name = self.rng.choice(list(self.stations.keys()))
                station = self.stations[name]
                res = yield station.request_service(customer)
                if not res:
                    self.analyzer.record_blocked(customer, self.env.now)
                    break
                wait, service_time = res
                self.analyzer.record_wait(customer, wait)
                self.analyzer.record_service(customer, service_time)
                if self.rng.random() < 0.4:
                    continue
                self.analyzer.record_departure(customer, self.env.now)
                break
        return self.env.process(proc())