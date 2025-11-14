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
        # capacity: Số lượng server (kẹp gắp) có sẵn
        # Resource tự động xếp hàng khách theo thứ tự đến và phân phối server
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
        # Khách đã chờ không gian K (từ food_station), thời gian đó được trừ vào patience
        time_spent_waiting_K = self.env.now - customer.start_wait_time
        # Thời gian kiên nhẫn còn lại = Tổng thời gian kiên nhẫn - Thời gian đã chờ K
        patience_remaining = customer.patience_time - time_spent_waiting_K
        
        # Nếu đã hết kiên nhẫn ngay khi vào chờ server (do chờ K quá lâu)
        if patience_remaining <= 0:
            customer.reneged = True  # Đánh dấu khách đã rời đi
            self.analyzer.record_reneging_event()  # Ghi nhận sự kiện reneging
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)
            return  # Khách rời đi, không được phục vụ

        # ========== BƯỚC 2: Yêu cầu server và chờ ==========
        # with self.servers.request() as req:
        #   - Tạo yêu cầu server (request)
        #   - Nếu server rảnh → Được server ngay
        #   - Nếu server bận → Tự động xếp hàng (FIFO - First In First Out)
        #   - Khi có server → Tự động được phục vụ
        with self.servers.request() as req:
            # Chờ: được server (req) HOẶC hết thời gian kiên nhẫn (timeout)
            # | : Toán tử OR trong SimPy - chờ một trong hai sự kiện xảy ra trước
            results = yield req | self.env.timeout(patience_remaining)

            # Ghi nhận thời gian chờ (dù được phục vụ hay không)
            # Wait time = Tổng thời gian từ khi bắt đầu chờ K đến khi được phục vụ hoặc rời đi
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)

            # ========== BƯỚC 3: Kiểm tra kết quả ==========
            if req not in results:
                # req không có trong results → timeout xảy ra trước (hết kiên nhẫn)
                # Khách đã chờ quá lâu mà vẫn chưa được server → Reneging
                customer.reneged = True
                self.analyzer.record_reneging_event()
                return  # Khách hàng rời hàng đợi, không được phục vụ

            # ========== BƯỚC 4: Đã được server phục vụ ==========
            # req có trong results → Được server trước khi hết thời gian kiên nhẫn
            
            # Lấy thời gian phục vụ riêng của khách này
            # Mỗi khách có service_time khác nhau (đã được tạo ngẫu nhiên khi khách đến)
            base_service_time = customer.service_times.get(
                self.station_name,  # Tên quầy (Meat, Seafood, ...)
                self.avg_service_time  # Nếu không có, dùng thời gian trung bình
            )
            
            # Sinh thời gian phục vụ thực tế theo phân phối exponential (phân phối mũ)
            # expovariate(1.0 / mean): Sinh số ngẫu nhiên với trung bình = mean
            # Phân phối exponential mô tả thời gian giữa các sự kiện (thời gian phục vụ)
            actual_service_time = random.expovariate(1.0 / base_service_time) 
            
            # Chờ thời gian phục vụ (khách đang lấy thức ăn)
            # Server được giữ trong suốt thời gian này
            yield self.env.timeout(actual_service_time)
            
            # Khi hết thời gian phục vụ, server tự động được giải phóng (do with statement)
            # Server quay lại pool và có thể phục vụ khách tiếp theo