# models/ros.py
"""
MÔ HÌNH HÀNG ĐỢI ROS (Random Order Serving - Phục vụ thứ tự ngẫu nhiên)

ROS chọn khách hàng ngẫu nhiên từ hàng đợi để phục vụ.
Điều này đảm bảo công bằng (fair) cho tất cả khách, không phân biệt
thời gian đến hay service_time.

LUỒNG HOẠT ĐỘNG:
1. Khách đến → Thêm vào list (không sắp xếp)
2. Server manager chọn khách ngẫu nhiên từ list
3. Phục vụ khách → Trả server về pool
4. Lặp lại

KHÁC BIỆT VỚI FCFS VÀ SJF:
- FCFS: SimPy.Resource tự động quản lý (FIFO - thứ tự đến)
- SJF: Priority queue (ưu tiên service_time ngắn)
- ROS: List đơn giản (chọn ngẫu nhiên - công bằng)
"""
import simpy
import random
from core.base_queue_system import BaseQueueSystem
from classes.customer import Customer

class ROSModel(BaseQueueSystem):
    """
    Hiện thực hàng đợi ROS (Random Order Serving - Phục vụ thứ tự ngẫu nhiên).
    
    Quản lý server thủ công để chọn khách hàng ngẫu nhiên.
    
    ĐẶC ĐIỂM:
    - Công bằng (fair): Tất cả khách có cơ hội được phục vụ như nhau
    - Không ưu tiên: Không phân biệt thời gian đến hay service_time
    - Đơn giản: Dùng list Python, không cần priority queue
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dùng Container (thay vì Resource) để quản lý không gian phục vụ thủ công
        # Container cho phép lấy/trả không gian phục vụ một cách linh hoạt
        # capacity: Tổng số không gian vật lý để đứng lấy thức ăn (serving space)
        # init: Số không gian ban đầu (tất cả đều rảnh)
        self.servers = simpy.Container(self.env, capacity=self.num_servers, init=self.num_servers)
        
        # Dùng list Python đơn giản (không cần priority queue như SJF)
        # Khách được thêm vào list theo thứ tự đến, nhưng được chọn ngẫu nhiên
        self.wait_list = []
        
        # Sự kiện để đánh thức 'server_manager' khi có khách mới đến
        self.customer_arrival = self.env.event()
        
        # Chạy tiến trình quản lý server (chạy nền - daemon process)
        self.env.process(self.server_manager())

    def serve(self, customer: Customer):
        """
        Khách hàng đến, tự thêm mình vào hàng đợi và chờ.
        
        LUỒNG:
        1. Thêm vào list (không sắp xếp, chỉ append)
        2. Đánh thức server_manager (có khách mới)
        3. Tạo event riêng cho khách này
        4. Chờ: được phục vụ HOẶC hết thời gian kiên nhẫn
        5. Nếu hết kiên nhẫn → Reneging
        """
        # ========== BƯỚC 1: Thêm vào hàng đợi ==========
        # Thêm khách vào list (không sắp xếp, chỉ append vào cuối)
        # Khác với SJF: Không cần priority queue, chỉ cần list đơn giản
        self.wait_list.append(customer)
        
        # ========== BƯỚC 2: Đánh thức server_manager ==========
        # Nếu event chưa được trigger → Trigger để server_manager biết có khách mới
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()
        
        # ========== BƯỚC 3: Tạo event riêng cho khách ==========
        # Mỗi khách có một event riêng
        # Lưu event vào customer để run_service() có thể trigger
        customer.served_event = self.env.event()
        
        # ========== BƯỚC 4: Chờ: ĐƯỢC PHỤC VỤ HOẶC HẾT KIÊN NHẪN ==========
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
        
        # ========== BƯỚC 5: Kiểm tra kết quả ==========
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
        2. Tìm khách ngẫu nhiên (ROS)
        3. Lấy server rảnh
        4. Phục vụ khách (chạy process con)
        5. Lặp lại
        
        KHÁC BIỆT VỚI FCFS VÀ SJF:
        - FCFS: SimPy.Resource tự động quản lý (không cần process này)
        - SJF: Chọn khách có service_time ngắn nhất (priority queue)
        - ROS: Chọn khách ngẫu nhiên (list đơn giản)
        """
        while True:
            # ========== BƯỚC 1: Kiểm tra hàng đợi ==========
            if not self.wait_list:
                # Hàng đợi rỗng, chờ khách mới đến
                # Chờ event customer_arrival (khi có khách mới đến sẽ trigger)
                yield self.customer_arrival
                self.customer_arrival = self.env.event()  # Reset event để dùng lần sau
                continue  # Quay lại đầu vòng lặp để kiểm tra lại

            # ========== BƯỚC 2: Tìm khách ngẫu nhiên ==========
            # Tìm khách ngẫu nhiên từ list (ROS - Random Order Serving)
            customer = self.find_customer_to_serve()
            if not customer:
                # Không tìm thấy khách hợp lệ (có thể tất cả đã reneged)
                # Chờ khách mới đến
                yield self.customer_arrival
                self.customer_arrival = self.env.event()  # Reset event
                continue

            # ========== BƯỚC 3: Lấy không gian phục vụ rảnh ==========
            # Chờ cho đến khi có ít nhất 1 không gian phục vụ rảnh
            # servers.get(1): Lấy 1 không gian phục vụ từ pool (giảm số không gian rảnh đi 1)
            yield self.servers.get(1)
            
            # ========== BƯỚC 4: Phục vụ khách ==========
            # Khởi chạy process con để phục vụ khách này
            # Process này sẽ:
            # - Ghi nhận wait_time
            # - Thông báo cho khách (trigger customer_served_or_reneged)
            # - Phục vụ (chờ service_time)
            # - Trả server về pool
            self.env.process(self.run_service(customer))

    def find_customer_to_serve(self):
        """
        Logic cốt lõi của ROS: Chọn ngẫu nhiên (Random Order Serving).
        
        KHÁC BIỆT VỚI FCFS VÀ SJF:
        - FCFS: SimPy.Resource tự động chọn khách đầu hàng (FIFO)
        - SJF: Chọn khách có service_time ngắn nhất (priority queue)
        - ROS: Chọn khách ngẫu nhiên (random) - công bằng cho tất cả
        
        LƯU Ý: Có thể chọn lại khách đã reneged, nhưng sẽ bỏ qua và chọn lại.
        """
        while self.wait_list:
            # ========== Chọn khách ngẫu nhiên ==========
            # random.randrange(len(self.wait_list)): Chọn index ngẫu nhiên
            # pop(idx): Lấy và xóa khách tại index đó
            # Điều này đảm bảo mỗi khách có cơ hội được chọn như nhau (công bằng)
            idx = random.randrange(len(self.wait_list))
            customer = self.wait_list.pop(idx)
            
            # ========== Kiểm tra khách đã reneged chưa ==========
            # Nếu khách đã rời đi (hết kiên nhẫn) → Bỏ qua, chọn khách khác
            if hasattr(customer, 'reneged') and customer.reneged:
                continue  # Bỏ qua khách này, chọn khách khác
            
            # ========== Tìm thấy khách hợp lệ ==========
            return customer  # Trả về khách để phục vụ
            
        return None  # Không tìm thấy khách hợp lệ (hàng đợi rỗng hoặc tất cả đã reneged)


    def run_service(self, customer: Customer):
        """
        Process con phục vụ 1 khách hàng.
        
        LUỒNG:
        1. Kiểm tra khách đã reneged chưa (TRƯỚC khi ghi wait_time)
        2. Ghi nhận wait_time (thời gian chờ) - chỉ khi chưa reneged
        3. Thông báo cho khách (trigger customer_served_or_reneged)
        4. Phục vụ (chờ service_time)
        5. Trả server về pool
        6. Đánh thức server_manager (có server rảnh)
        """
        # ========== BƯỚC 1: Kiểm tra khách đã reneged chưa ==========
        # Nếu khách đã rời đi (hết kiên nhẫn) → Trả server ngay, không ghi wait_time
        # Lưu ý: Wait_time đã được ghi trong serve() khi reneging
        if hasattr(customer, 'reneged') and customer.reneged:
            yield self.servers.put(1)  # Trả server về pool
            return  # Không phục vụ, không ghi wait_time
        
        # ========== BƯỚC 2: Ghi nhận thời gian chờ ==========
        # Wait time = Tổng thời gian từ khi bắt đầu chờ K đến khi được phục vụ
        # Chỉ ghi khi khách chưa reneged (đã được kiểm tra ở trên)
        wait_time = self.env.now - customer.start_wait_time
        self.analyzer.record_wait_time(self.station_name, wait_time)
        
        # ========== BƯỚC 3: Thông báo cho khách ==========
        # Trigger event để khách biết đã được phục vụ
        # Điều này dừng timeout của Reneging trong serve() của khách
        if hasattr(customer, 'served_event') and customer.served_event:
            customer.served_event.succeed()
        
        # ========== BƯỚC 4: Phục vụ khách ==========
        # Lấy service_time của khách này
        base_service_time = customer.service_times.get(
            self.station_name, 
            self.avg_service_time
        )
        
        # Áp dụng logic customer types:
        # - 'indulgent': Nhân đôi serve_time
        if customer.customer_type == 'indulgent':
            base_service_time *= 2.0
        
        # - 'erratic': Tăng service_time cho khách sau
        # Logic erratic - khi erratic customer được phục vụ,
        # các khách đang chờ sẽ có service_time tăng thêm
        if customer.customer_type == 'erratic':
            import config
            erratic_delay = getattr(config, 'ERRATIC_DELAY_AMOUNT', 0.2)
            # Tăng service_time cho tất cả khách đang chờ trong wait_list
            for waiting_customer in self.wait_list:
                if hasattr(waiting_customer, 'service_times'):
                    station_time = waiting_customer.service_times.get(
                        self.station_name,
                        self.avg_service_time
                    )
                    waiting_customer.service_times[self.station_name] = (
                        station_time + erratic_delay
                    )
        
        # Sinh thời gian phục vụ thực tế theo phân phối exponential
        actual_service_time = random.expovariate(1.0 / base_service_time)
        
        # Chờ thời gian phục vụ (khách đang lấy thức ăn)
        yield self.env.timeout(actual_service_time)
        
        # ========== BƯỚC 5: Trả không gian phục vụ về pool ==========
        # Phục vụ xong, trả không gian phục vụ về pool (tăng số không gian rảnh lên 1)
        yield self.servers.put(1)
        
        # ========== BƯỚC 6: Đánh thức server_manager ==========
        # Có server rảnh, đánh thức server_manager để phục vụ khách tiếp theo
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()