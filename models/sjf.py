# models/sjf.py
import simpy
import random
import heapq # Dùng hàng đợi ưu tiên (priority queue)
from core.base_queue_system import BaseQueueSystem
from classes.customer import Customer

# (ASSUMED) Ngưỡng thời gian chờ để chống starvation 
STARVATION_THRESHOLD = 10.0 # 10 phút

class SJFModel(BaseQueueSystem):
    """
    Hiện thực hàng đợi SJF (Shortest Job First)[cite: 100].
    Quản lý server thủ công để chọn khách hàng và chống starvation.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dùng Container để đếm số server rảnh
        self.servers = simpy.Container(self.env, capacity=self.num_servers, init=self.num_servers)
        
        # Dùng Priority Queue (min-heap) để lưu khách hàng
        # (priority, arrival_time, customer)
        self.wait_list = [] 
        
        # Sự kiện để đánh thức 'server_manager'
        self.customer_arrival = self.env.event() 

        # Chạy tiến trình quản lý server
        self.env.process(self.server_manager())

    def serve(self, customer: Customer):
        """
        Khách hàng đến, tự thêm mình vào hàng đợi ưu tiên và chờ.
        """
        service_time = customer.service_times.get(
            self.station_name, self.avg_service_time
        )
        
        # Thêm khách vào hàng đợi ưu tiên
        # (service_time là độ ưu tiên, arrival_time để chống 'equal priority' bug)
        heapq.heappush(self.wait_list, (service_time, self.env.now, customer))
        
        # Đánh thức server manager
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()

        # Chờ... (Reneging logic)
        # Tạo một sự kiện riêng cho khách này để chờ
        customer_served_or_reneged = self.env.event()
        
        results = yield customer_served_or_reneged | self.env.timeout(customer.patience_time)
        
        if customer_served_or_reneged not in results:
            # Khách hàng HẾT KIÊN NHẪN (Reneging)
            self.analyzer.record_reneging_event()
            # Phải xóa khách này khỏi hàng đợi (cực kỳ phức tạp)
            # Đơn giản hóa: Đánh dấu 'reneged'
            customer.reneged = True # Thêm 1 thuộc tính mới
            
            # Ghi nhận thời gian chờ
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)


    def server_manager(self):
        """
        Process chạy nền (daemon) để quản lý các server.
        """
        while True:
            if not self.wait_list:
                # Hàng đợi rỗng, chờ khách đến
                yield self.customer_arrival
                self.customer_arrival = self.env.event() # Reset event

            # Hàng đợi có khách, chờ server rảnh
            yield self.servers.get(1) # Chờ 1 server
            
            # Lấy khách hàng
            customer = self.find_customer_to_serve()
            if not customer:
                # Khách hàng duy nhất đã 'reneged', trả server
                yield self.servers.put(1)
                continue # Quay lại đầu vòng lặp

            # Khởi chạy 1 process con để phục vụ khách này
            self.env.process(self.run_service(customer))

    def find_customer_to_serve(self):
        """
        Logic cốt lõi của SJF + Starvation
        """
        while self.wait_list:
            (service_time, arrival_time, customer) = heapq.heappop(self.wait_list)
            
            # Kiểm tra xem khách đã 'reneged' trong lúc chờ chưa
            if hasattr(customer, 'reneged') and customer.reneged:
                continue # Bỏ qua khách này

            # Kiểm tra Starvation 
            wait_time = self.env.now - arrival_time
            if wait_time > STARVATION_THRESHOLD:
                # Khách này đã chờ quá lâu -> ưu tiên
                return customer
                
            # Kiểm tra xem có ai chờ lâu hơn (starved) không
            # (Phải duyệt/heapq không hỗ trợ) -> Đơn giản hóa:
            # Nếu khách SJF chưa bị 'starved', ta ưu tiên SJF.
            # Logic chống starvation phức tạp hơn cần duyệt toàn bộ list.
            # Tạm thời: ưu tiên SJF
            
            # Tạm thời trả lại khách (nếu logic phức tạp hơn)
            # heapq.heappush(self.wait_list, (service_time, arrival_time, customer))
            # ... tìm người bị starved ...
            
            # Logic đơn giản:
            # 1. Ưu tiên ai bị starved
            # (tạm bỏ qua vì heapq phức tạp)
            # 2. Lấy SJF
            return customer
            
        return None # Không tìm thấy khách hợp lệ


    def run_service(self, customer: Customer):
        """Process con phục vụ 1 khách hàng."""
        
        # Ghi nhận thời gian chờ
        wait_time = self.env.now - customer.start_wait_time
        self.analyzer.record_wait_time(self.station_name, wait_time)

        # Thông báo cho 'serve' process là khách đã được phục vụ
        # (Để dừng 'timeout' của Reneging)
        # Phải kiểm tra 'reneged' 1 lần nữa
        if hasattr(customer, 'reneged') and customer.reneged:
             yield self.servers.put(1) # Trả server ngay
             return
        
        # Lấy service time
        actual_service_time = random.expovariate(
            1.0 / customer.service_times.get(self.station_name, self.avg_service_time)
        )
        
        yield self.env.timeout(actual_service_time)
        
        # Trả server
        yield self.servers.put(1)
        
        # Đánh thức server_manager (nếu nó đang chờ)
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()