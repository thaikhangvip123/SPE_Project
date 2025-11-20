# models/sjf.py
"""
MÔ HÌNH HÀNG ĐỢI SJF (Shortest Job First - Công việc ngắn nhất trước)

SJF ưu tiên phục vụ khách có thời gian phục vụ ngắn nhất trước.
Điều này giúp giảm thời gian chờ trung bình, nhưng có thể gây "starvation"
(khách có service time dài bị chờ quá lâu).

LUỒNG HOẠT ĐỘNG:
1. Khách đến → Thêm vào priority queue (sắp xếp theo service_time)
2. Server manager chọn khách có service_time ngắn nhất
3. Nếu khách chờ quá lâu (starvation) → Ưu tiên phục vụ
4. Phục vụ khách → Trả server về pool
5. Lặp lại

KHÁC BIỆT VỚI FCFS:
- FCFS: Dùng SimPy.Resource (tự động quản lý FIFO)
- SJF: Quản lý thủ công với priority queue (heapq) để chọn khách ưu tiên
"""
import simpy
import random
import heapq  # Dùng hàng đợi ưu tiên (priority queue - min-heap)
from core.base_queue_system import BaseQueueSystem
from classes.customer import Customer

# Ngưỡng thời gian chờ để chống starvation (chống đói)
# Nếu khách chờ quá 10 phút → Ưu tiên phục vụ (bất kể service_time)
STARVATION_THRESHOLD = 10.0  # 10 phút

class SJFModel(BaseQueueSystem):
    """
    Hiện thực hàng đợi SJF (Shortest Job First - Công việc ngắn nhất trước).
    
    Quản lý server thủ công để:
    1. Chọn khách có service_time ngắn nhất (SJF)
    2. Chống starvation (ưu tiên khách chờ quá lâu)
    
    KHÁC BIỆT VỚI FCFS:
    - FCFS: SimPy.Resource tự động quản lý (FIFO)
    - SJF: Quản lý thủ công với priority queue + server manager
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dùng Container (thay vì Resource) để quản lý server thủ công
        # Container cho phép lấy/trả server một cách linh hoạt
        # capacity: Tổng số server, init: Số server ban đầu (tất cả đều rảnh)
        self.servers = simpy.Container(self.env, capacity=self.num_servers, init=self.num_servers)
        
        # Priority Queue (min-heap) để lưu khách hàng chờ
        # Mỗi phần tử: (priority, arrival_time, customer)
        # - priority = service_time (ưu tiên service_time ngắn nhất)
        # - arrival_time: Thời điểm đến (để chống starvation)
        # - customer: Đối tượng khách hàng
        # heapq là min-heap → Phần tử nhỏ nhất ở đầu (service_time ngắn nhất)
        self.wait_list = [] 
        
        # Sự kiện để đánh thức 'server_manager' khi có khách mới đến
        # Khi khách đến, trigger event này để server_manager biết có khách mới
        self.customer_arrival = self.env.event() 
        
        # Chạy tiến trình quản lý server (chạy nền - daemon process)
        # Process này chạy liên tục, chọn khách và phân phối server
        self.env.process(self.server_manager())

    def serve(self, customer: Customer):
        """
        Khách hàng đến, tự thêm mình vào hàng đợi ưu tiên và chờ.
        
        LUỒNG:
        1. Lấy service_time của khách (để xác định độ ưu tiên)
        2. Thêm vào priority queue (sắp xếp theo service_time)
        3. Đánh thức server_manager (có khách mới)
        4. Tạo event riêng cho khách này (để server_manager thông báo khi được phục vụ)
        5. Chờ: được phục vụ HOẶC hết thời gian kiên nhẫn
        6. Nếu hết kiên nhẫn → Reneging
        """
        # Lấy service_time của khách này tại quầy hiện tại
        # Service_time xác định độ ưu tiên (service_time ngắn = ưu tiên cao)
        service_time = customer.service_times.get(
            self.station_name,  # Tên quầy (Meat, Seafood, ...)
            self.avg_service_time  # Nếu không có, dùng thời gian trung bình
        )
        
        # Áp dụng logic customer types:
        # - 'indulgent': Nhân đôi serve_time
        if customer.customer_type == 'indulgent':
            service_time *= 2.0
        
        # - 'erratic': Tăng service_time cho khách sau (đang chờ)
        # Lưu ý: Logic erratic - khi erratic customer vào queue,
        # các khách đang chờ sẽ có service_time tăng thêm
        if customer.customer_type == 'erratic':
            import config
            erratic_delay = getattr(config, 'ERRATIC_DELAY_AMOUNT', 0.2)
            # Tăng service_time cho tất cả khách đang chờ trong wait_list
            for i, (prio, arr_time, waiting_customer) in enumerate(self.wait_list):
                if hasattr(waiting_customer, 'service_times'):
                    station_time = waiting_customer.service_times.get(
                        self.station_name,
                        self.avg_service_time
                    )
                    waiting_customer.service_times[self.station_name] = (
                        station_time + erratic_delay
                    )
                    # Cập nhật lại priority trong queue (nếu cần)
                    # Lưu ý: Không cần cập nhật priority vì đây là SJF,
                    # priority dựa trên service_time ban đầu khi vào queue
        
        # Thêm khách vào priority queue (min-heap)
        # Format: (priority, arrival_time, customer)
        # - priority = service_time (ưu tiên service_time ngắn nhất)
        # - arrival_time = env.now (thời điểm đến, để chống starvation)
        # - customer: Đối tượng khách hàng
        heapq.heappush(self.wait_list, (service_time, self.env.now, customer))
        
        # Đánh thức server_manager (nếu đang chờ khách mới)
        # Nếu event chưa được trigger → Trigger để server_manager biết có khách mới
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()

        # ========== TẠO SỰ KIỆN RIÊNG CHO KHÁCH NÀY ==========
        # Mỗi khách có một event riêng
        # Khi server_manager chọn khách này để phục vụ, sẽ trigger event này
        # Khách chờ event này được trigger (được phục vụ)
        customer.served_event = self.env.event()
        
        # ========== CHỜ: ĐƯỢC PHỤC VỤ HOẶC HẾT KIÊN NHẪN ==========
        patience_remaining = customer.patience_time
        
        # Nếu đã hết kiên nhẫn ngay khi vào chờ server
        if patience_remaining <= 0:
            customer.reneged = True
            self.analyzer.record_reneging_event(self.station_name)
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)
            return
        
        # Chờ: customer.served_event (được phục vụ) HOẶC timeout (hết kiên nhẫn)
        # | : Toán tử OR trong SimPy - chờ một trong hai sự kiện xảy ra trước
        results = yield customer.served_event | self.env.timeout(patience_remaining)
        
        # ========== KIỂM TRA KẾT QUẢ ==========
        if customer.served_event not in results:
            # customer.served_event không có trong results → timeout xảy ra trước
            # Khách đã chờ quá lâu mà vẫn chưa được phục vụ → Reneging
            self.analyzer.record_reneging_event(self.station_name)
            customer.reneged = True  # Đánh dấu khách đã rời đi
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)

        # Dọn dẹp: Xóa event (không cần thiết nữa)
        customer.served_event = None


    def server_manager(self):
        """
        Process chạy nền (daemon) để quản lý các server.
        
        Process này chạy liên tục, thực hiện:
        1. Chờ khách đến (nếu hàng đợi rỗng)
        2. Tìm khách ưu tiên (SJF hoặc bị starvation)
        3. Lấy server rảnh
        4. Phục vụ khách (chạy process con)
        5. Lặp lại
        
        KHÁC BIỆT VỚI FCFS:
        - FCFS: SimPy.Resource tự động quản lý (không cần process này)
        - SJF: Cần process này để chọn khách ưu tiên thủ công
        """
        while True:
            # ========== BƯỚC 1: Kiểm tra hàng đợi ==========
            if not self.wait_list:
                # Hàng đợi rỗng, chờ khách mới đến
                # Chờ event customer_arrival (khi có khách mới đến sẽ trigger)
                yield self.customer_arrival
                self.customer_arrival = self.env.event()  # Reset event để dùng lần sau
                continue  # Quay lại đầu vòng lặp để kiểm tra lại

            # ========== BƯỚC 2: Tìm khách ưu tiên ==========
            # Tìm khách có service_time ngắn nhất HOẶC bị starvation
            customer = self.find_customer_to_serve()
            if not customer:
                # Không tìm thấy khách hợp lệ (có thể tất cả đã reneged)
                # Chờ khách mới đến
                yield self.customer_arrival
                self.customer_arrival = self.env.event()  # Reset event
                continue

            # ========== BƯỚC 3: Lấy server rảnh ==========
            # Chờ cho đến khi có ít nhất 1 server rảnh
            # servers.get(1): Lấy 1 server từ pool (giảm số server rảnh đi 1)
            yield self.servers.get(1)
            
            # ========== BƯỚC 4: Phục vụ khách ==========
            # Khởi chạy process con để phục vụ khách này
            # Process này sẽ:
            # - Ghi nhận wait_time
            # - Thông báo cho khách (trigger customer.served_event)
            # - Phục vụ (chờ service_time)
            # - Trả server về pool
            self.env.process(self.run_service(customer))


    def find_customer_to_serve(self):
        """
        Logic cốt lõi của SJF + Starvation (chống đói).
        
        Tìm khách để phục vụ theo thứ tự ưu tiên:
        1. Khách bị starvation (chờ quá lâu) → Ưu tiên cao nhất
        2. Khách có service_time ngắn nhất (SJF) → Ưu tiên thứ hai
        
        LƯU Ý: Logic hiện tại đơn giản hóa - chỉ kiểm tra starvation cho khách đầu queue.
        Logic đầy đủ cần duyệt toàn bộ queue để tìm khách bị starvation nặng nhất.
        """
        while self.wait_list:
            # Lấy khách đầu priority queue (có service_time ngắn nhất)
            # heappop: Lấy và xóa phần tử nhỏ nhất (min-heap)
            (service_time, arrival_time, customer) = heapq.heappop(self.wait_list)
            
            # ========== Kiểm tra khách đã reneged chưa ==========
            # Nếu khách đã rời đi (hết kiên nhẫn) → Bỏ qua, tìm khách khác
            if hasattr(customer, 'reneged') and customer.reneged:
                continue  # Bỏ qua khách này, lấy khách tiếp theo

            # ========== Kiểm tra Starvation (chống đói) ==========
            # Tính thời gian khách đã chờ
            wait_time = self.env.now - arrival_time
            
            if wait_time > STARVATION_THRESHOLD:
                # Khách này đã chờ quá lâu (> 10 phút) → Ưu tiên phục vụ
                # Bất kể service_time dài hay ngắn, khách chờ quá lâu sẽ được ưu tiên
                # Điều này ngăn chặn starvation (khách bị chờ vô hạn)
                return customer
                
            # ========== Logic SJF (nếu chưa bị starvation) ==========
            # Nếu khách này chưa bị starvation, kiểm tra xem có khách nào khác
            # bị starvation nặng hơn không.
            # 
            # LƯU Ý: Logic hiện tại đơn giản hóa - chỉ kiểm tra khách đầu queue.
            # Logic đầy đủ cần:
            # 1. Duyệt toàn bộ queue để tìm khách bị starvation nặng nhất
            # 2. Nếu có → Ưu tiên khách đó
            # 3. Nếu không → Ưu tiên SJF (khách hiện tại có service_time ngắn nhất)
            #
            # Tạm thời: Ưu tiên SJF (khách hiện tại)
            return customer
            
        return None  # Không tìm thấy khách hợp lệ (hàng đợi rỗng hoặc tất cả đã reneged)


    def run_service(self, customer: Customer):
        """Process con phục vụ 1 khách hàng."""
        
        # Kiểm tra khách đã reneged chưa (TRƯỚC khi ghi wait_time)
        # Nếu khách đã rời đi (hết kiên nhẫn) → Trả server ngay, không ghi wait_time
        # Lưu ý: Wait_time đã được ghi trong serve() khi reneging
        if hasattr(customer, 'reneged') and customer.reneged:
             yield self.servers.put(1) # Trả server ngay
             return
        
        # Ghi nhận thời gian chờ - chỉ khi khách chưa reneged
        wait_time = self.env.now - customer.start_wait_time
        self.analyzer.record_wait_time(self.station_name, wait_time)

        # Thông báo cho 'serve' process là khách đã được phục vụ
        # (Để dừng 'timeout' của Reneging)
        if hasattr(customer, 'served_event') and customer.served_event:
            customer.served_event.succeed()
        
        # Lấy service time
        base_service_time = customer.service_times.get(
            self.station_name, 
            self.avg_service_time
        )
        
        # Áp dụng logic customer types:
        # - 'indulgent': Nhân đôi serve_time
        if customer.customer_type == 'indulgent':
            base_service_time *= 2.0
        
        # - 'erratic': Tăng service_time cho khách sau
        # Logic này được xử lý trong serve() khi khách được thêm vào queue
        # (tăng service_time cho khách đang chờ trong wait_list)
        erratic_delay = 0.0
        if customer.customer_type == 'erratic':
            import config
            erratic_delay = getattr(config, 'ERRATIC_DELAY_AMOUNT', 0.2)
            # Tăng service_time cho tất cả khách đang chờ trong wait_list
            for (_, _, waiting_customer) in self.wait_list:
                if hasattr(waiting_customer, 'service_times'):
                    station_time = waiting_customer.service_times.get(
                        self.station_name,
                        self.avg_service_time
                    )
                    waiting_customer.service_times[self.station_name] = (
                        station_time + erratic_delay
                    )
        
        actual_service_time = random.expovariate(1.0 / base_service_time)
        
        yield self.env.timeout(actual_service_time)
        
        # Trả server
        yield self.servers.put(1)
        
        # Đánh thức server_manager (nếu nó đang chờ)
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()