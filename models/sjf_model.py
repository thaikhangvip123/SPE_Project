from .base_model import BaseModel


class SJFModel(BaseModel):
    """
    Shortest Job First (SJF): Phục vụ khách hàng có thời gian phục vụ ngắn nhất trước.
    
    Logic:
    1. Chọn quầy có thời gian phục vụ trung bình ngắn nhất (hoặc dựa trên routing_mode)
    2. Kiểm tra starvation: nếu khách hàng đã chờ quá lâu, ưu tiên phục vụ ngay
    3. Yêu cầu phục vụ
    4. Sau khi phục vụ, quyết định tiếp tục hay ra về
    """
    def __init__(self, env, stations, analyzer, rng, 
                 prob_matrices=None, routing_mode='random', 
                 continue_probability=0.4, station_order=None, buffet_system=None,
                 starvation_threshold=5.0):
        super().__init__(env, stations, analyzer, rng, prob_matrices, 
                        routing_mode, continue_probability, station_order, buffet_system)
        self.starvation_threshold = starvation_threshold  # Ngưỡng thời gian chờ để tránh starvation
    
    def select_station_sjf(self, customer):
        """
        Chọn quầy theo SJF: quầy có thời gian phục vụ ngắn nhất.
        Nếu khách hàng đã chờ quá lâu (starvation), chọn quầy có ít người nhất.
        
        Args:
            customer: Đối tượng Customer
            
        Returns:
            str: Tên quầy được chọn
        """
        available = [s for s in self.stations.keys() 
                    if not customer.has_visited(s) and self.stations[s].can_enter()]
        
        if not available:
            return None
        
        # Kiểm tra starvation: nếu khách hàng đã chờ quá lâu, ưu tiên phục vụ ngay
        wait_time = customer.get_wait_time(self.env.now)
        if wait_time > self.starvation_threshold:
            # Chọn quầy có ít người nhất để phục vụ nhanh
            return min(available, key=lambda s: self.stations[s].customers_in_system())
        
        # Bình thường: chọn quầy có thời gian phục vụ trung bình ngắn nhất
        return min(available, key=lambda k: self.stations[k].avg_service_time)
    
    def serve_customer(self, customer):
        def proc():
            while True:
                # Chọn quầy theo logic SJF (có kiểm tra starvation)
                name = self.select_station_sjf(customer)
                
                if name is None:
                    self.analyzer.record_departure(customer, self.env.now)
                    break
                
                station = self.stations[name]
                
                # Yêu cầu phục vụ
                res = yield station.request_service(customer)
                
                if not res:
                    self.analyzer.record_blocked(customer, self.env.now)
                    available = [s for s in self.stations.keys() 
                               if not customer.has_visited(s) and self.stations[s].can_enter()]
                    if not available:
                        break
                    continue
                
                wait, service_time = res
                self.analyzer.record_wait(customer, wait)
                self.analyzer.record_service(customer, service_time)
                customer.mark_visited(name)
                
                # Quyết định tiếp tục hay ra về
                if self.rng.random() < self.continue_probability:
                    continue
                else:
                    self.analyzer.record_departure(customer, self.env.now)
                    break
        
        return self.env.process(proc())