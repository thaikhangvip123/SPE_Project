# config.py

"""
File cấu hình tập trung cho toàn bộ mô phỏng.
Các giá trị giả định (MARKED AS ASSUMED) cần được xác nhận
lại từ yêu cầu hoặc báo cáo chi tiết.
"""

# Thời gian mô phỏng tổng cộng (đơn vị: phút)
UNTIL_TIME = 1000.0

# (ASSUMED) Tốc độ khách đến (khách/phút) cho mỗi cổng
ARRIVAL_RATES = {
    0: 12,  # Cổng "Arrived 0"
    1: 10   # Cổng "Arrived 1"
}

# (ASSUMED) Thời gian kiên nhẫn mặc định
# Lưu ý: Patience_time được reset ở mỗi quầy mới
# Nếu wait time trung bình ~7 phút, patience_time nên >= 10-15 phút để tránh reneging quá nhiều
DEFAULT_PATIENCE_TIME = 10.0 # Khách sẽ rời hàng đợi nếu chờ quá 20 phút (tăng từ 15 để giảm reneging)

# (ASSUMED) Tỷ lệ phân bố các loại khách hàng
CUSTOMER_TYPE_DISTRIBUTION = {
    'normal': 0.70,      # 70% khách bình thường
    'indulgent': 0.10,   # 10% khách tham lam (nhân đôi serve_time)
    'impatient': 0.15,   # 15% khách thiếu kiên nhẫn (patience_time thấp)
    'erratic': 0.05      # 5% khách thất thường (tăng service_time cho khách sau)
}

# (ASSUMED) Hệ số điều chỉnh patience_time cho từng loại khách
PATIENCE_TIME_FACTORS = {
    'normal': 1.0,       # Giữ nguyên
    'indulgent': 1.0,    # Giữ nguyên
    'impatient': 0.5,    # Giảm còn 50% (kiên nhẫn kém)
    'erratic': 1.0       # Giữ nguyên
}

# (ASSUMED) Lượng service_time tăng thêm cho khách sau khi có erratic customer
ERRATIC_DELAY_AMOUNT = 0.2  # Tăng thêm 0.2 phút cho mỗi khách sau

# (ASSUMED) Thời gian phục vụ (lấy thức ăn) trung bình cho 1 khách
# tại các quầy. Dùng để sinh ngẫu nhiên service time cho SJF.
DEFAULT_SERVICE_TIMES = {
    'Meat': 0.7,
    'Seafood': 0.5,
    'Dessert': 0.8,
    'Fruit':0.3
}

# Cấu hình các quầy thức ăn (Stations)
# Dựa trên Hình 1 (trang 4) và Hình 2 (trang 6)
STATIONS = {
    'Meat': {
        'servers': 5,            # 10 Tongs
        'capacity_K': 10,         # (ASSUMED) Giới hạn không gian
        'discipline': 'SJF',      # SJF
        'avg_service_time':0.5   # (ASSUMED) 
    },
    'Seafood': {
        'servers': 7,             # 5 Tongs
        'capacity_K': 10,         # (ASSUMED)
        'discipline': 'SJF',      # SJF
        'avg_service_time': 0.3   # (ASSUMED)
    },
    'Dessert': {
        'servers': 7,             # 7 Ladle
        'capacity_K': 10,         # (ASSUMED)
        'discipline': 'ROS',      # ROS
        'avg_service_time': 0.5   # (ASSUMED)
    },
    'Fruit': {
        'servers':10,              # Grab by hand (ASSUMED = 7)
        'capacity_K': 10,         # (ASSUMED)
        'discipline': 'ROS',      # ROS
        'avg_service_time': 0.3   # (ASSUMED)
    }
}

"""
Ma trận xác suất (Dựa trên Hình 2, trang 6)


Do đó, GIẢ ĐỊNH logic như sau:
1. 'initial': Xác suất chọn quầy đầu tiên (dựa trên Hình 2).
2. 'next_action': Xác suất chọn "Lấy thêm" (More) hoặc "Về" (Exit).
3. 'transition': Xác suất chọn quầy tiếp theo, NẾU đã chọn "More".
"""
PROB_MATRICES = {
    # Xác suất chọn quầy ban đầu
    'initial': {
        # Cổng 0
        0: {
            'Meat': 0.4,      #
            'Seafood': 0.3,   #
            'Dessert': 0.2,  #
            'Fruit': 0.2     #
        },
        # Cổng 1
        1: {
            'Meat': 0.3,      #
            'Seafood': 0.4,   #
            'Dessert': 0.15,  #
            'Fruit': 0.15     #
        }
    },
    
    # (ASSUMED) Xác suất "Lấy thêm" hay "Về"
    'next_action': {
        'More': 0.7, # 70% lấy thêm
        'Exit': 0.3  # 30% ra về
    },
    
    # (ASSUMED) Xác suất chọn quầy tiếp theo (nếu chọn 'More')
    # Phân bố đều cho các quầy #######FIX########
    'transition': { # Nếu các quầy đều thì bỏ về (balking)
        'Meat': 0.25,
        'Seafood': 0.25,
        'Dessert': 0.25,
        'Fruit': 0.25
    }
}