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
                discipline_model=model # Tiêm model vào
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

            new_customer = Customer(
                id=customer_id,
                arrival_gate=gate_id,
                arrival_time=self.env.now,
                customer_type='normal',
                patience_time=self.config.DEFAULT_PATIENCE_TIME,
                service_times=customer_service_times
            )
            # Thêm thuộc tính 'reneged'
            # new_customer.reneged = False 

            self.env.process(self.customer_lifecycle(new_customer))

    def customer_lifecycle(self, customer: Customer):
        """
        Hành trình của khách hàng (Sửa lỗi đếm trùng).
        """
        
        station_name = self.choose_initial_section(customer.arrival_gate)
        visited_stations = set()

        while station_name is not None:
            if station_name in visited_stations:
                station_name = self.choose_next_action(customer, visited_stations)
                continue

            station = self.stations[station_name]
            visited_stations.add(station_name)
            
            yield self.env.process(station.serve(customer))
            
            # Nếu khách đã 'reneged', dừng hành trình ngay
            if customer.reneged:
                break # Thoát khỏi vòng lặp 'while'

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

    def choose_next_action(self, customer: Customer, visited_stations: set):
        """
        Quyết định: (a) đi lấy thêm đồ hay (b) ra về. [cite: 277, 278]
        """
        # Quyết định: Lấy thêm hay Về? (Hình 2 [cite: 118])
        prob_map = self.prob_matrices['next_action']
        action = random.choices(
            list(prob_map.keys()), 
            weights=list(prob_map.values()), 
            k=1
        )[0]
        
        if action == 'Exit':
            return None # [cite: 280]
        
        prob_map_transition = self.prob_matrices['transition']
        
        available_stations = []
        available_probs = []
        
        for station, prob in prob_map_transition.items():
            if station not in visited_stations:
                available_stations.append(station)
                available_probs.append(prob)
        
        if not available_stations:
            return None # Không còn quầy nào để đi

        # Chuẩn hóa lại xác suất
        total_prob = sum(available_probs)
        normalized_probs = [p / total_prob for p in available_probs]
        
        return random.choices(available_stations, weights=normalized_probs, k=1)[0]

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