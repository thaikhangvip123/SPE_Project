# models/ros.py
import simpy
import random
from core.base_queue_system import BaseQueueSystem
from classes.customer import Customer

class ROSModel(BaseQueueSystem):
    """
    Hiện thực hàng đợi ROS (Random Order Serving)[cite: 99].
    Quản lý server thủ công để chọn khách hàng ngẫu nhiên.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.servers = simpy.Container(self.env, capacity=self.num_servers, init=self.num_servers)
        self.wait_list = [] # Dùng list Python đơn giản
        self.customer_arrival = self.env.event()
        self.env.process(self.server_manager())

    def serve(self, customer: Customer):
        """
        Khách hàng đến, tự thêm mình vào hàng đợi và chờ.
        """
        self.wait_list.append(customer)
        
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()
        
        # Logic Reneging
        customer_served_or_reneged = self.env.event()
        results = yield customer_served_or_reneged | self.env.timeout(customer.patience_time)
        
        if customer_served_or_reneged not in results:
            self.analyzer.record_reneging_event()
            customer.reneged = True 
            wait_time = self.env.now - customer.start_wait_time
            self.analyzer.record_wait_time(self.station_name, wait_time)

    def server_manager(self):
        """
        Process chạy nền quản lý server.
        """
        while True:
            if not self.wait_list:
                yield self.customer_arrival
                self.customer_arrival = self.env.event()

            yield self.servers.get(1) # Chờ 1 server
            
            customer = self.find_customer_to_serve()
            if not customer:
                yield self.servers.put(1)
                continue
            
            self.env.process(self.run_service(customer))

    def find_customer_to_serve(self):
        """
        Logic cốt lõi của ROS: Chọn ngẫu nhiên.
        """
        while self.wait_list:
            # Chọn 1 khách ngẫu nhiên
            idx = random.randrange(len(self.wait_list))
            customer = self.wait_list.pop(idx)
            
            if hasattr(customer, 'reneged') and customer.reneged:
                continue # Bỏ qua
            
            return customer # Tìm thấy
        return None # Hàng đợi rỗng


    def run_service(self, customer: Customer):
        """Process con phục vụ 1 khách hàng."""
        
        wait_time = self.env.now - customer.start_wait_time
        self.analyzer.record_wait_time(self.station_name, wait_time)
        
        if hasattr(customer, 'reneged') and customer.reneged:
             yield self.servers.put(1)
             return
        
        actual_service_time = random.expovariate(
            1.0 / customer.service_times.get(self.station_name, self.avg_service_time)
        )
        
        yield self.env.timeout(actual_service_time)
        
        yield self.servers.put(1) # Trả server
        
        if not self.customer_arrival.triggered:
            self.customer_arrival.succeed()