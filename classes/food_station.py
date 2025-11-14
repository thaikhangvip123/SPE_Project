# classes/food_station.py
import simpy
import random
from .customer import Customer
from .analysis import Analysis
from core.base_queue_system import BaseQueueSystem # Import lớp base

class FoodStation:
    """
    Đại diện cho một hàng đợi M/M/c/K vật lý.
    Phiên bản này được refactor để sử dụng mô hình kỷ luật (model) 
    được tiêm vào (dependency injection).
    """
    def __init__(self, env: simpy.Environment, name: str, 
                 capacity_K: int, analyzer: Analysis, 
                 discipline_model: BaseQueueSystem): # <--- CHỈ NHẬN 5 THAM SỐ NÀY
        
        self.env = env
        self.name = name                 
        self.analyzer = analyzer
        self.discipline_model = discipline_model # Model (SJF, FCFS...) được tiêm vào
        
        # 'queue_space' vẫn ở đây, để theo dõi không gian vật lý (K)
        self.capacity_K = capacity_K     
        self.queue_space = simpy.Container(env, capacity=capacity_K, init=capacity_K)

    def serve(self, customer: Customer):
        """
        Tiến trình mô phỏng.
        Xử lý logic chờ không gian (K) (Balking).
        Sau đó ủy quyền logic chờ server (c) (Reneging) cho discipline_model.
        """
        
        self.analyzer.record_attempt(self.name)
        
        # 1. Kiểm tra không gian vật lý (K)
        get_space_req = self.queue_space.get(1)
        
        # Khách hàng bắt đầu chờ K
        customer.start_wait_time = self.env.now
        
        results = yield get_space_req | self.env.timeout(customer.patience_time)

        if get_space_req not in results:
            # Hết kiên nhẫn khi chờ K (Balking)
            customer.reneged = True
            self.analyzer.record_blocking_event(self.name) 
            return # Khách hàng rời đi

        # ---- Đã có chỗ trong quầy (K) ----
        
        # 2. Ủy quyền cho mô hình (FCFS, SJF, ROS) xử lý
        #    Logic chờ server (c) và Reneging
        yield self.env.process(self.discipline_model.serve(customer))
        
        # 3. Phục vụ xong (hoặc reneged), trả lại không gian K
        yield self.queue_space.put(1)