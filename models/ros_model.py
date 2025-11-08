from .base_model import BaseModel


class ROSModel(BaseModel):
    """
    Random Order Serving (ROS): Phục vụ khách hàng theo thứ tự ngẫu nhiên.
    
    Logic:
    1. Chọn quầy ngẫu nhiên (dựa trên routing_mode và probability matrices)
    2. Yêu cầu phục vụ tại quầy đó
    3. Sau khi phục vụ xong, quyết định tiếp tục hay ra về (dựa trên continue_probability)
    4. Lặp lại cho đến khi khách hàng quyết định ra về hoặc bị chặn
    """
    def serve_customer(self, customer):
        def proc():
            while True:
                # Chọn quầy thức ăn dựa trên routing mode
                name = self.select_station(customer)
                
                # Nếu không còn quầy nào khả dụng, khách hàng ra về
                if name is None:
                    self.analyzer.record_departure(customer, self.env.now)
                    break
                
                station = self.stations[name]
                
                # Yêu cầu phục vụ tại quầy này
                res = yield station.request_service(customer)
                
                # Nếu bị chặn (hết chỗ), ghi nhận và thử quầy khác hoặc ra về
                if not res:
                    self.analyzer.record_blocked(customer, self.env.now)
                    # Nếu tất cả quầy đều đầy, khách hàng ra về
                    available = [s for s in self.stations.keys() 
                               if not customer.has_visited(s) and self.stations[s].can_enter()]
                    if not available:
                        break
                    continue
                
                # Ghi nhận thời gian chờ và phục vụ
                wait, service_time = res
                self.analyzer.record_wait(customer, wait)
                self.analyzer.record_service(customer, service_time)
                
                # Đánh dấu quầy này đã được thăm
                customer.mark_visited(name)
                
                # Quyết định tiếp tục hay ra về
                if self.rng.random() < self.continue_probability:
                    # Tiếp tục đến quầy khác
                    continue
                else:
                    # Ra về
                    self.analyzer.record_departure(customer, self.env.now)
                    break
        
        return self.env.process(proc())