# models/fcfs.py
import simpy
import random
from core.base_queue_system import BaseQueueSystem
from classes.customer import Customer

class FCFSModel(BaseQueueSystem):
    """
    Hiện thực hàng đợi FCFS (First Come First Served) 
    sử dụng 'simpy.Resource'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # simpy.Resource tự động quản lý hàng đợi FCFS [cite: 219]
        self.servers = simpy.Resource(self.env, capacity=self.num_servers)

    def serve(self, customer: Customer):
        """
        Tiến trình phục vụ FCFS. Xử lý chờ server (c) và Reneging.
        """
        # Tính thời gian kiên nhẫn còn lại
        time_spent_waiting_K = self.env.now - customer.start_wait_time
        patience_remaining = customer.patience_time - time_spent_waiting_K
        if patience_remaining <= 0:
            return # Hết kiên nhẫn ngay khi vào

        # Yêu cầu 1 server (kẹp gắp)
        with self.servers.request() as req:
            results = yield req | self.env.timeout(patience_remaining)

            # Ghi nhận thời gian chờ (dù được phục vụ hay không)
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)

            if req not in results:
                # Hết kiên nhẫn khi chờ server (Reneging)
                self.analyzer.record_reneging_event()
                return # Khách hàng rời hàng đợi

            # ---- Đã được server phục vụ (c) ----
            
            # Lấy thời gian phục vụ riêng của khách này
            base_service_time = customer.service_times.get(
                self.station_name, self.avg_service_time
            )
            
            # Phân phối mũ
            actual_service_time = random.expovariate(1.0 / base_service_time) 
            
            yield self.env.timeout(actual_service_time)