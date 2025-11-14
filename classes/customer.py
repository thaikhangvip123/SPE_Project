# classes/customer.py

class Customer:
    """
    Đại diện cho một "thực thể" (entity) di chuyển trong hệ thống. [cite: 233]
    Chủ yếu là một cấu trúc dữ liệu để lưu trữ trạng thái. [cite: 234]
    """
    def __init__(self, id, arrival_gate, arrival_time, customer_type, patience_time, service_times):
        
        # --- Thuộc tính chính từ báo cáo ---
        self.id = id                         # Mã định danh duy nhất [cite: 239]
        self.arrival_gate = arrival_gate     # Ghi nhận cổng vào (0 hay 1) [cite: 236]
        self.arrival_time = arrival_time     # Thời điểm khách xuất hiện [cite: 237]
        self.customer_type = customer_type   # 'normal', 'indulgent', 'impatient', ... [cite: 240]
        self.patience_time = patience_time   # Ngưỡng kiên nhẫn để "Reneging" 
        
        # Dict: {'Meat': 5.0, 'Seafood': 7.0, ...}
        # Lưu thời gian LẤY THỨC ĂN (service time) trung bình của khách này 
        # tại mỗi quầy [cite: 238]
        self.service_times = service_times
        
        # --- Thuộc tính theo dõi trạng thái ---
        self.current_station = None          # Quầy hiện tại khách đang ở
        self.start_wait_time = 0.0           # Thời điểm bắt đầu chờ (để tính wait time)
        self.served_event = None             # Sự kiện để server báo cho customer
        self.reneged = False
        self.my_turn_event = None

    def __str__(self):
        """Hàm hỗ trợ cho việc logging, in ra ID khách hàng."""
        return f"Customer_{self.id}({self.customer_type})"