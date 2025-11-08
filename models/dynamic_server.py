from .base_model import BaseModel
import simpy


class DynamicServerModel(BaseModel):
    """
    Dynamic Server: Phân bổ server động giữa các hàng đợi.
    
    Logic:
    1. Tổng hợp tất cả server vào một pool chung
    2. Khách hàng đến trước được phục vụ trước (FIFO)
    3. Server sau khi phục vụ xong sẽ kiểm tra hàng đợi nào đông nhất để phục vụ tiếp
    4. Chọn khách hàng trong hàng đợi theo nguyên tắc FIFO
    """
    def __init__(self, env, stations, analyzer, rng, 
                 prob_matrices=None, routing_mode='random', 
                 continue_probability=0.4, station_order=None, buffet_system=None):
        super().__init__(env, stations, analyzer, rng, prob_matrices, 
                        routing_mode, continue_probability, station_order, buffet_system)
        
        # Tính tổng số server từ tất cả các quầy
        total_servers = sum(station.c for station in stations.values())
        
        # Tạo một resource pool chung cho tất cả server
        self.shared_server_pool = simpy.Resource(env, capacity=total_servers)
        
        # Queue chung cho tất cả khách hàng (FIFO)
        self.global_queue = []
    
    def serve_customer(self, customer):
        """
        Phục vụ khách hàng sử dụng server pool chung.
        Khách hàng đến trước được phục vụ trước (FIFO).
        """
        def proc():
            while True:
                # Chọn quầy thức ăn (dựa trên routing mode)
                station_name = self.select_station(customer)
                
                if station_name is None:
                    self.analyzer.record_departure(customer, self.env.now)
                    break
                
                station = self.stations[station_name]
                
                # Kiểm tra capacity K của quầy
                if not station.can_enter():
                    self.analyzer.record_blocked(customer, self.env.now)
                    available = [s for s in self.stations.keys() 
                               if not customer.has_visited(s) and self.stations[s].can_enter()]
                    if not available:
                        break
                    continue
                
                # Yêu cầu server từ pool chung (FIFO tự động)
                arrive = self.env.now
                with self.shared_server_pool.request() as req:
                    # Chờ đến lượt (FIFO)
                    yield req
                    
                    # Tính thời gian chờ
                    wait = self.env.now - arrive
                    
                    # Lấy thức ăn tại quầy này
                    service_time = customer.sample_service_time(station_name, self.rng, station.avg_service_time)
                    yield self.env.timeout(service_time)
                    
                    # Ghi nhận số liệu
                    self.analyzer.record_wait(customer, wait)
                    self.analyzer.record_service(customer, service_time)
                    customer.mark_visited(station_name)
                    
                    # Quyết định tiếp tục hay ra về
                    if self.rng.random() < self.continue_probability:
                        continue
                    else:
                        self.analyzer.record_departure(customer, self.env.now)
                        break
        
        return self.env.process(proc())