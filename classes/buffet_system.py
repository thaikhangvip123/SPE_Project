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
        # Chỉ 'indulgent' không được quay lại quầy đã đi qua
        # Các loại khác có thể quay lại quầy cũ
        visited_stations = set() if customer.customer_type == 'indulgent' else None

        # ========== BƯỚC 1: Chọn quầy đầu tiên kèm kiểm tra K ==========
        station_name, no_available = self.choose_initial_section(customer.arrival_gate)
        if station_name is None:
            if no_available:
                customer.reneged = True
            return

        # ========== VÒNG LẶP: Đi lấy thức ăn tại các quầy ==========
        while station_name is not None:
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
            next_station, reason = self.choose_next_action(customer, visited_stations)
            if next_station is None:
                if reason == 'no_available':
                    customer.reneged = True
                break
            station_name = next_station
        
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
        Trả về tuple (station_name, no_available). station_name = None khi không
        có quầy nào còn chỗ.
        """
        # Lấy ma trận xác suất cho cổng này
        prob_map = self.prob_matrices['initial'][gate_id]
        return self._select_station_with_capacity(prob_map)

    def choose_next_action(self, customer: Customer, visited_stations):
        """
        Quyết định: (a) đi lấy thêm đồ hay (b) ra về. [cite: 277, 278]
        
        LƯU Ý: 
        - 'indulgent': Không được quay lại quầy đã đi (visited_stations là set)
        - Các loại khác: Có thể quay lại quầy cũ (visited_stations là None)
        Trả về tuple (station_name_or_none, reason):
            - reason = 'exit'  → khách quyết định ra về
            - reason = 'no_available' → muốn lấy thêm nhưng tất cả quầy hợp lệ đều đầy
            - reason = None → có quầy mới để tới
        """
        # Quyết định: Lấy thêm hay Về? (Hình 2 [cite: 118])
        prob_map = self.prob_matrices['next_action']
        action = random.choices(
            list(prob_map.keys()), 
            weights=list(prob_map.values()), 
            k=1
        )[0]
        
        if action == 'Exit':
            return None, 'exit'  # Khách quyết định ra về
        
        # Nếu chọn "More", chọn quầy tiếp theo theo logic phân bổ mới
        prob_map_transition = self.prob_matrices['transition']
        next_station, no_available = self._select_station_with_capacity(
            prob_map_transition,
            visited_stations
        )
        if next_station is None and no_available:
            return None, 'no_available'
        return next_station, None

    def _select_station_with_capacity(self, prob_map, visited_stations=None):
        """
        Chọn quầy dựa theo xác suất. Nếu quầy được chọn đang đầy K, đặt xác suất
        của quầy đó về 0, chia đều phần xác suất bị mất cho các quầy còn lại
        (đảm bảo tổng = 1) rồi chọn lại. Lặp đến khi tìm được quầy còn chỗ
        hoặc tất cả xác suất đều về 0 (mọi quầy đầy) → trả None, True.
        """
        current_probs = {}
        for station, prob in prob_map.items():
            if visited_stations is not None and station in visited_stations:
                continue
            current_probs[station] = prob

        if not current_probs:
            return None, False  # Không có quầy hợp lệ (do visited hoặc không cấu hình)

        full_attempts = []
        full_set = set()
        while True:
            # A={ i ∣ p[i] ​> 0}
            active_stations = [s for s, p in current_probs.items() if p > 0]
            if not active_stations:
                if full_attempts:
                    self._record_balking_for_stations(full_attempts)
                    return None, True  # Tất cả xác suất đã về 0 do quầy đầy
                return None, False  # Không có xác suất dương nào (không phải do đầy)

            weights = [current_probs[s] for s in active_stations]

            # chosen∼DiscreteDistribution(P) Where: 𝑃 = { 𝑝[𝑖] ∣ 𝑖 ∈ 𝐴}
            chosen = random.choices(active_stations, weights=weights, k=1)[0]

            if self.stations[chosen].queue_space.level > 0:
                return chosen, False

            # Quầy đã đầy: chuyển xác suất sang các quầy còn lại
            full_attempts.append(chosen)
            full_set.add(chosen)

            prob_loss = current_probs[chosen]
            current_probs[chosen] = 0.0

            remaining = [s for s in current_probs if s not in full_set]
            if not remaining:
                self._record_balking_for_stations(full_attempts)
                return None, True  # Không còn quầy nào để nhận phần xác suất mất

            share = prob_loss / len(remaining)
            for station in remaining:
                current_probs[station] += share

    def _record_balking_for_stations(self, stations):
        """Ghi nhận attempt + balking khi mọi quầy hợp lệ đều đầy."""
        unique = set(stations)
        for station_name in unique:
            self.analyzer.record_attempt(station_name)
            self.analyzer.record_blocking_event(station_name)
        if unique:
            self.analyzer.record_customer_balk()

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