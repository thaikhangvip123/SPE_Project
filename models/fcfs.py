# models/fcfs.py
"""
MÔ HÌNH HÀNG ĐỢI FCFS (First Come First Served - Ai đến trước phục vụ trước)

FCFS là mô hình hàng đợi đơn giản nhất: khách hàng được phục vụ theo thứ tự đến.
SimPy.Resource tự động quản lý hàng đợi FCFS, không cần logic phức tạp.

LUỒNG HOẠT ĐỘNG:
1. Khách đến → Yêu cầu server
2. Nếu server rảnh → Được phục vụ ngay
3. Nếu server bận → Xếp hàng chờ (theo thứ tự đến)
4. Khi server rảnh → Phục vụ khách đầu hàng
5. Nếu chờ quá lâu (hết patience) → Khách rời đi (Reneging)
"""
import simpy
import random
from core.base_queue_system import BaseQueueSystem
from classes.customer import Customer

class FCFSModel(BaseQueueSystem):
    """
    Hiện thực hàng đợi FCFS (First Come First Served - Ai đến trước phục vụ trước) 
    sử dụng 'simpy.Resource'.
    
    SimPy.Resource tự động quản lý:
    - Hàng đợi theo thứ tự đến (FIFO - First In First Out)
    - Phân phối server cho khách hàng
    - Không cần logic phức tạp để quản lý thứ tự
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # SimPy.Resource tự động quản lý hàng đợi FCFS
        # capacity: Số lượng không gian vật lý để đứng lấy thức ăn (serving space)
        # Resource tự động xếp hàng khách theo thứ tự đến và phân phối không gian phục vụ
        self.servers = simpy.Resource(self.env, capacity=self.num_servers)

    def serve(self, customer: Customer):
        """
        Tiến trình phục vụ FCFS. Xử lý chờ server (c) và Reneging (rời đi do hết kiên nhẫn).
        
        LUỒNG:
        1. Tính thời gian kiên nhẫn còn lại (sau khi đã chờ không gian K)
        2. Yêu cầu server (tự động xếp hàng nếu server bận)
        3. Chờ: được server HOẶC hết thời gian kiên nhẫn
        4. Nếu được server → Phục vụ (service time)
        5. Nếu hết kiên nhẫn → Reneging (rời đi)
        """
        # ========== BƯỚC 1: Tính thời gian kiên nhẫn còn lại ==========
        # Patience_time được reset khi khách vào quầy (FoodStation)
        patience_remaining = customer.patience_time
        
        # Nếu đã hết kiên nhẫn ngay khi vào chờ server
        if patience_remaining <= 0:
            customer.reneged = True  # Đánh dấu khách đã rời đi
            self.analyzer.record_reneging_event(self.station_name)  # Ghi nhận sự kiện reneging
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)
            return  # Khách rời đi, không được phục vụ

        # ========== BƯỚC 2: Yêu cầu không gian phục vụ và chờ ==========
        # with self.servers.request() as req:
        #   - Tạo yêu cầu không gian phục vụ (request)
        #   - Nếu không gian rảnh → Được phục vụ ngay
        #   - Nếu không gian bận → Tự động xếp hàng (FIFO - First In First Out)
        #   - Khi có không gian → Tự động được phục vụ
        with self.servers.request() as req:
            # Chờ: được không gian phục vụ (req) HOẶC hết thời gian kiên nhẫn (timeout)
            # | : Toán tử OR trong SimPy - chờ một trong hai sự kiện xảy ra trước
            results = yield req | self.env.timeout(patience_remaining)

            # Ghi nhận thời gian chờ (dù được phục vụ hay không)
            # Wait time = Tổng thời gian từ khi bắt đầu chờ K đến khi được phục vụ hoặc rời đi
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)

            # ========== BƯỚC 3: Kiểm tra kết quả ==========
            if req not in results:
                # req không có trong results → timeout xảy ra trước (hết kiên nhẫn)
                # Khách đã chờ quá lâu mà vẫn chưa được không gian phục vụ → Reneging
                customer.reneged = True
                self.analyzer.record_reneging_event(self.station_name)
                return  # Khách hàng rời hàng đợi, không được phục vụ

            # ========== BƯỚC 4: Đã được không gian phục vụ ==========
            # req có trong results → Được không gian phục vụ trước khi hết thời gian kiên nhẫn
            
            # Lấy thời gian phục vụ riêng của khách này
            # Mỗi khách có service_time khác nhau (đã được tạo ngẫu nhiên khi khách đến)
            base_service_time = customer.service_times.get(
                self.station_name,  # Tên quầy (Meat, Seafood, ...)
                self.avg_service_time  # Nếu không có, dùng thời gian trung bình
            )
            
            # Áp dụng logic customer types:
            # - 'indulgent': Nhân đôi serve_time
            if customer.customer_type == 'indulgent':
                base_service_time *= 2.0
            
            # - 'erratic': Tăng service_time cho khách sau
            # Lưu ý: Trong FCFS, các khách đang chờ ở Resource queue,
            # nên logic erratic được xử lý khi khách này được phục vụ
            # (tăng service_time cho khách đang chờ trong queue)
            erratic_delay = 0.0
            if customer.customer_type == 'erratic':
                import config
                erratic_delay = getattr(config, 'ERRATIC_DELAY_AMOUNT', 0.2)
                # Tăng service_time cho các khách đang chờ trong queue
                # Lưu ý: SimPy Resource không cho phép truy cập queue trực tiếp,
                # nên logic này được xử lý ở mức cao hơn (trong FoodStation)
            
            # Sinh thời gian phục vụ thực tế theo phân phối exponential (phân phối mũ)
            # expovariate(1.0 / mean): Sinh số ngẫu nhiên với trung bình = mean
            # Phân phối exponential mô tả thời gian giữa các sự kiện (thời gian phục vụ)
            actual_service_time = random.expovariate(1.0 / base_service_time) 
            
            # Chờ thời gian phục vụ (khách đang lấy thức ăn)
            # Không gian phục vụ được giữ trong suốt thời gian này
            yield self.env.timeout(actual_service_time)
            
            # Khi hết thời gian phục vụ, không gian phục vụ tự động được giải phóng (do with statement)
            # Không gian phục vụ quay lại pool và có thể phục vụ khách tiếp theo