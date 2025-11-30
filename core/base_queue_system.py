# core/base_queue_system.py
import simpy
from abc import ABC, abstractmethod
from classes.customer import Customer
from classes.analysis import Analysis

class BaseQueueSystem(ABC):
    """
    Lớp cơ sở trừu tượng (Abstract Base Class) cho tất cả mô hình hàng đợi.
    Định nghĩa giao diện 'serve' chung.
    """
    def __init__(self, env: simpy.Environment, num_servers: int, 
                 avg_service_time: float, analyzer: Analysis, station_name: str):
        self.env = env
        # num_servers: Số lượng không gian vật lý để đứng lấy thức ăn (serving space)
        self.num_servers = num_servers
        self.avg_service_time = avg_service_time
        self.analyzer = analyzer
        self.station_name = station_name # Cần để lấy service time của khách

    @abstractmethod
    def serve(self, customer: Customer):
        """
        Tiến trình trừu tượng cho việc phục vụ khách hàng.
        Bao gồm logic chờ không gian phục vụ (serving space) và xử lý "Reneging".
        Logic chờ không gian tổng thể (K) được xử lý ở FoodStation.
        """
        pass