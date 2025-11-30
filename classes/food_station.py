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
                 discipline_model: BaseQueueSystem, config=None): # Thêm config parameter
        
        self.env = env
        self.name = name                 
        self.analyzer = analyzer
        self.discipline_model = discipline_model # Model (SJF, FCFS...) được tiêm vào
        self.config = config  # Lưu config để reset patience_time
        
        # 'queue_space' vẫn ở đây, để theo dõi không gian vật lý (K)
        self.capacity_K = capacity_K     
        self.queue_space = simpy.Container(env, capacity=capacity_K, init=capacity_K)

    def serve(self, customer: Customer):
        """
        Tiến trình mô phỏng.
        Xử lý logic chờ không gian tổng thể (K) (Balking).
        Sau đó ủy quyền logic chờ không gian phục vụ (serving space) (Reneging) cho discipline_model.
        """
        
        self.analyzer.record_attempt(self.name)
        
        # 1. Kiểm tra và lấy không gian vật lý tổng thể (K) - BALKING
        # Balking: Nếu K đầy → Khách bỏ về ngay lập tức (không chờ)
        # SimPy Container: 
        #   - init=K nghĩa là ban đầu có K đơn vị trong container (K chỗ trống)
        #   - level = số đơn vị hiện có trong container (số chỗ còn trống)
        #   - level = 0 → đã lấy hết (đầy, không còn chỗ)
        #   - level = K → chưa lấy gì (rỗng, còn K chỗ)
        # Vậy: available_space = level (số chỗ còn trống)
        # K bao gồm: không gian đứng lấy thức ăn (serving space) + không gian đứng xếp hàng
        if self.queue_space.level == 0:
            # Queue đã đầy (level = 0) → Balking ngay (không chờ patience_time)
            customer.reneged = True
            self.analyzer.record_blocking_event(self.name)
            self.analyzer.record_customer_balk()
            return  # Khách hàng bỏ về ngay
        
        # 2. Lấy không gian K (tổng thể)
        # Lưu ý: Nếu available_space > 0, get(1) sẽ lấy ngay (không chờ)
        # Nếu có race condition (nhiều khách cùng lúc), get(1) sẽ chờ
        # Thời gian chờ đó sẽ được tính vào time_spent_waiting_K
        yield self.queue_space.get(1)

        # 3. Reset patience_time sau khi khách THỰC SỰ vào quầy
        if self.config:
            patience_factor = self.config.PATIENCE_TIME_FACTORS.get(
                customer.customer_type, 
                1.0
            )
            customer.patience_time = self.config.DEFAULT_PATIENCE_TIME * patience_factor
        
        # Đánh dấu thời điểm bắt đầu chờ không gian phục vụ (sau khi đã có chỗ K)
        customer.start_wait_time = self.env.now
        
        # 4. Ủy quyền cho mô hình xử lý chờ không gian phục vụ (serving space) và RENEGING
        # Reneging: Khách chờ không gian phục vụ quá patience_time → Rời hàng
        yield self.env.process(self.discipline_model.serve(customer))
        
        # 5. Phục vụ xong (hoặc reneged), trả lại không gian K
        yield self.queue_space.put(1)