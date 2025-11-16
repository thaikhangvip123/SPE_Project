# classes/buffet_system.py
import simpy
import random
from .customer import Customer
from .food_station import FoodStation
from .analysis import Analysis
from core.queue_system_factory import QueueSystemFactory

class BuffetSystem:
    """
    Đây là bộ não của toàn bộ mô phỏng. 
    Chứa logic chính, điều khiển luồng thời gian và quản lý các thành phần. [cite: 198]
    """
    def __init__(self, env: simpy.Environment, analyzer: Analysis, config):
        self.env = env                 # [cite: 200]
        self.analyzer = analyzer       # [cite: 204]
        self.config = config           # File config (sẽ tạo sau)
        
        self.stations = {}             # Dict chứa các đối tượng FoodStation 
        self.arrival_rates = config.ARRIVAL_RATES # 
        self.prob_matrices = config.PROB_MATRICES # 

        # Khởi tạo Factory
        self.factory = QueueSystemFactory()
        
        # Khởi tạo các FoodStation
        for name, cfg in config.STATIONS.items():
            
            # 1. Dùng Factory tạo ra mô hình (FCFS, SJF...)
            model = self.factory.create_queue_model(
                env=env,
                config=cfg,
                analyzer=analyzer,
                station_name=name
            )
            
            # 2. Tạo FoodStation và tiêm model vào
            self.stations[name] = FoodStation(
                env=env,
                name=name,
                capacity_K=cfg['capacity_K'],
                analyzer=analyzer,
                discipline_model=model, # Tiêm model vào
                config=config  # Truyền config để reset patience_time
            )

            # Ghi nhận station với analyzer
            self.analyzer.add_station(name)

    def generate_customers(self, gate_id):
        """
        Một "tiến trình" SimPy chạy song song. [cite: 207]
        Nó tạo ra khách hàng mới theo phân phối Poisson (exponential inter-arrival). 
        """
        arrival_rate = self.arrival_rates[gate_id] # (lambda)
        
        while True:
            # 1. Tính thời gian chờ cho khách tiếp theo
            inter_arrival_time = random.expovariate(arrival_rate)
            yield self.env.timeout(inter_arrival_time)
            
            # 2. Tạo khách hàng
            customer_id = self.analyzer.total_arrivals
            self.analyzer.record_arrival() # [cite: 171]
            
            # Tạo service times ngẫu nhiên cho khách này (cho SJF)
            customer_service_times = {}
            for station, base_time in self.config.DEFAULT_SERVICE_TIMES.items():
                # Giả định thời gian của khách dao động 50%-150% so với trung bình
                customer_service_times[station] = random.uniform(base_time * 0.5, base_time * 1.5)

            # Chọn loại khách hàng dựa trên phân phối xác suất
            customer_types = list(self.config.CUSTOMER_TYPE_DISTRIBUTION.keys())
            customer_weights = list(self.config.CUSTOMER_TYPE_DISTRIBUTION.values())
            customer_type = random.choices(customer_types, weights=customer_weights, k=1)[0]
            
            # Tính patience_time dựa trên loại khách hàng
            patience_factor = self.config.PATIENCE_TIME_FACTORS.get(
                customer_type, 
                1.0  # Mặc định giữ nguyên
            )
            patience_time = self.config.DEFAULT_PATIENCE_TIME * patience_factor

            new_customer = Customer(
                id=customer_id,
                arrival_gate=gate_id,
                arrival_time=self.env.now,
                customer_type=customer_type,
                patience_time=patience_time,
                service_times=customer_service_times
            )
            # Thêm thuộc tính 'reneged'
            # new_customer.reneged = False 

            self.env.process(self.customer_lifecycle(new_customer))

    def customer_lifecycle(self, customer: Customer):
        """
        Hành trình của khách hàng.
        
        LUỒNG:
        1. Kiểm tra tất cả quầy đầy → Balking ngay
        2. Chọn quầy đầu tiên
        3. Đến quầy (có thể bị balking nếu quầy đầy)
        4. Lấy thức ăn (có thể reneging nếu chờ server quá lâu)
        5. Quyết định: Lấy thêm hay ra về
        6. Lặp lại hoặc thoát
        """
        # ========== BƯỚC 1: Kiểm tra TẤT CẢ quầy đều đầy → Balking ngay ==========
        # Theo mô tả: "Nếu tất cả các quầy đều đã đầy thì khách hàng đến sẽ bỏ về (fail)"
        # SimPy Container: level = 0 nghĩa là đầy (không còn chỗ)
        if all(station.queue_space.level == 0 for station in self.stations.values()):
            customer.reneged = True
            # Ghi nhận balking ở tất cả các quầy (hoặc có thể tạo event riêng ở system level)
            for station_name in self.stations.keys():
                self.analyzer.record_blocking_event(station_name)
            return
        
        # ========== BƯỚC 2: Chọn quầy đầu tiên dựa trên ma trận xác suất ==========
        station_name = self.choose_initial_section(customer.arrival_gate)
        
        # Chỉ 'indulgent' không được quay lại quầy đã đi qua
        # Các loại khác có thể quay lại quầy cũ
        visited_stations = set() if customer.customer_type == 'indulgent' else None

        # ========== VÒNG LẶP: Đi lấy thức ăn tại các quầy ==========
        while station_name is not None:
            # Kiểm tra visited_stations chỉ cho indulgent
            if visited_stations is not None and station_name in visited_stations:
                station_name = self.choose_next_action(customer, visited_stations)
                continue

            station = self.stations[station_name]
            
            # Đánh dấu quầy đã đi qua (chỉ cho indulgent)
            if visited_stations is not None:
                visited_stations.add(station_name)
            
            # Đến quầy và lấy thức ăn (có thể bị balking hoặc reneging)
            yield self.env.process(station.serve(customer))
            
            # Nếu khách đã balking hoặc reneging, dừng hành trình ngay
            if customer.reneged:
                break  # Thoát khỏi vòng lặp

            # Quyết định: Lấy thêm hay ra về
            station_name = self.choose_next_action(customer, visited_stations)
        
        # --- LOGIC SỬA LỖI ---
        # Kiểm tra xem vòng lặp 'while' kết thúc
        # là do 'break' (reneged) hay do 'station_name = None' (exit)
        
        if customer.reneged:
            # Khách hàng này đã bỏ về (reneged)
            # Chúng ta KHÔNG ghi nhận 'exit'
            pass 
        else:
            # Khách hàng này thoát thành công
            system_time = self.env.now - customer.arrival_time
            self.analyzer.record_exit(system_time)

    def choose_initial_section(self, gate_id):
        """
        Chọn quầy đầu tiên dựa trên ma trận xác suất của cổng vào. 
        """
        # Lấy ma trận xác suất cho cổng này
        prob_map = self.prob_matrices['initial'][gate_id]
        
        # Lấy list các quầy và xác suất tương ứng
        stations = list(prob_map.keys())
        probs = list(prob_map.values())
        
        # Trả về một lựa chọn dựa trên trọng số xác suất
        return random.choices(stations, weights=probs, k=1)[0]

    def choose_next_action(self, customer: Customer, visited_stations):
        """
        Quyết định: (a) đi lấy thêm đồ hay (b) ra về. [cite: 277, 278]
        
        LƯU Ý: 
        - 'indulgent': Không được quay lại quầy đã đi (visited_stations là set)
        - Các loại khác: Có thể quay lại quầy cũ (visited_stations là None)
        """
        # Quyết định: Lấy thêm hay Về? (Hình 2 [cite: 118])
        prob_map = self.prob_matrices['next_action']
        action = random.choices(
            list(prob_map.keys()), 
            weights=list(prob_map.values()), 
            k=1
        )[0]
        
        if action == 'Exit':
            return None  # Khách quyết định ra về
        
        # Nếu chọn "More", chọn quầy tiếp theo
        prob_map_transition = self.prob_matrices['transition']
        
        available_stations = []
        available_probs = []
        
        for station, prob in prob_map_transition.items():
            # Chỉ 'indulgent' mới bị giới hạn visited_stations
            if visited_stations is None or station not in visited_stations:
                available_stations.append(station)
                available_probs.append(prob)
        
        if not available_stations:
            return None  # Không còn quầy nào để đi (cho indulgent)

        # Chuẩn hóa lại xác suất
        total_prob = sum(available_probs)
        if total_prob > 0:
            normalized_probs = [p / total_prob for p in available_probs]
            return random.choices(available_stations, weights=normalized_probs, k=1)[0]
        else:
            return None

    def run(self, until_time):
        """
        Phương thức khởi động. 
        """
        # Khởi chạy các generator cho từng cổng 
        for gate_id in self.arrival_rates.keys():
            self.env.process(self.generate_customers(gate_id))
        
        # Chạy mô phỏng cho đến mốc thời gian
        print(f"--- Bat dau mo phong (Until={until_time}) ---")
        self.env.run(until=until_time)
        print("--- Ket thuc mo phong ---")