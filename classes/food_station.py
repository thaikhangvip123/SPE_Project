import simpy
import random

class FoodStation:
    """
    Đại diện cho một quầy thức ăn (hàng đợi M/M/c/K).
    
    Thuộc tính:
    - name: Tên quầy (ví dụ: 'fruit', 'meat')
    - c: Số server (số kẹp gắp/muỗng có thể dùng đồng thời)
    - K: Sức chứa tối đa (giới hạn không gian vật lý)
    - avg_service_time: Thời gian phục vụ trung bình (1/μ)
    - resource: SimPy Resource quản lý hàng đợi và server (FCFS tự động)
    """
    def __init__(self, name, env, c=1, K=float('inf'), avg_service_time=1.0, rng=None):
        self.name = name  # Tên quầy
        self.env = env  # Môi trường SimPy
        self.c = c  # Số server (capacity của resource)
        self.capacity_K = K  # Sức chứa tối đa (giới hạn không gian)
        self.avg_service_time = avg_service_time  # Thời gian phục vụ trung bình
        self.resource = simpy.Resource(env, capacity=c)  # Resource quản lý server (FCFS)
        self.rng = rng or random  # Random number generator

    def customers_in_system(self):
        """
        Đếm số khách hàng hiện tại trong hệ thống (đang được phục vụ + đang chờ).
        
        Returns:
            int: Tổng số khách hàng trong quầy
        """
        return self.resource.count + len(self.resource.queue)

    def can_enter(self):
        """
        Kiểm tra xem quầy còn chỗ không (chưa đạt capacity K).
        
        Returns:
            bool: True nếu còn chỗ, False nếu đầy
        """
        return self.customers_in_system() < self.capacity_K

    def request_service(self, customer):
        """
        Yêu cầu phục vụ cho một khách hàng.
        
        Args:
            customer: Đối tượng Customer
            
        Returns:
            Process: SimPy process xử lý việc phục vụ
        """
        return self.env.process(self._serve(customer))

    def _serve(self, customer):
        """
        Logic phục vụ khách hàng (FCFS - First Come First Served).
        
        Args:
            customer: Đối tượng Customer
            
        Yields:
            SimPy events (timeout, resource request)
            
        Returns:
            tuple: (wait_time, service_time) nếu thành công, False nếu bị chặn hoặc timeout
        """
        # Kiểm tra capacity K trước khi vào hàng đợi
        if not self.can_enter():
            return False
        
        arrive = self.env.now  # Thời điểm khách hàng đến
        
        # Yêu cầu một server (FCFS tự động bởi SimPy Resource)
        with self.resource.request() as req:
            # Chờ đến lượt hoặc hết kiên nhẫn (patience_time)
            patience = customer.patience_time
            results = yield req | self.env.timeout(patience)
            
            # Nếu timeout (hết kiên nhẫn), khách hàng rời đi
            if req not in results:
                return False
            
            # Tính thời gian chờ
            wait = self.env.now - arrive
            
            # Lấy thức ăn (thời gian phục vụ)
            service_time = customer.sample_service_time(self.name, self.rng, self.avg_service_time)
            yield self.env.timeout(service_time)
            
            # Trả về thời gian chờ và thời gian phục vụ
            return wait, service_time