# configs/all_fcfs.py

"""
File cấu hình: Tất cả quầy sử dụng FCFS (First Come First Served)
"""

# Seed cho random để đảm bảo kết quả tái lập được
RANDOM_SEED = 200

# Thời gian mô phỏng tổng cộng (đơn vị: phút)
UNTIL_TIME = 1000.0

# Tốc độ khách đến (khách/phút) cho mỗi cổng
ARRIVAL_RATES = {
    0: 12,  # Cổng "Arrived 0"
    1: 10   # Cổng "Arrived 1"
}

# Thời gian kiên nhẫn mặc định
DEFAULT_PATIENCE_TIME = 10.0

# Tỷ lệ phân bố các loại khách hàng
CUSTOMER_TYPE_DISTRIBUTION = {
    'normal': 0.70,      # 70% khách bình thường
    'indulgent': 0.10,   # 10% khách tham lam (nhân đôi serve_time)
    'impatient': 0.15,   # 15% khách thiếu kiên nhẫn (patience_time thấp)
    'erratic': 0.05      # 5% khách thất thường (tăng service_time cho khách sau)
}

# Hệ số điều chỉnh patience_time cho từng loại khách
PATIENCE_TIME_FACTORS = {
    'normal': 1.0,       # Giữ nguyên
    'indulgent': 1.0,    # Giữ nguyên
    'impatient': 0.5,    # Giảm còn 50% (kiên nhẫn kém)
    'erratic': 1.0       # Giữ nguyên
}

# Lượng service_time tăng thêm cho khách sau khi có erratic customer
ERRATIC_DELAY_AMOUNT = 0.2

# Thời gian phục vụ (lấy thức ăn) trung bình cho 1 khách tại các quầy
DEFAULT_SERVICE_TIMES = {
    'Meat': 0.7,
    'Seafood': 0.5,
    'Dessert': 0.8,
    'Fruit': 0.3
}

# Cấu hình các quầy thức ăn (Stations)
# TẤT CẢ QUẦY SỬ DỤNG FCFS
# - 'servers': Không gian vật lý để đứng lấy thức ăn (serving space)
# - 'capacity_K': Tổng không gian vật lý = không gian đứng lấy thức ăn + không gian đứng xếp hàng
STATIONS = {
    'Meat': {
        'servers': 5,            # Không gian vật lý để đứng lấy thức ăn
        'capacity_K': 10,         # Tổng không gian vật lý (bao gồm cả không gian xếp hàng)
        'discipline': 'FCFS',     # FCFS
        'avg_service_time': 0.5
    },
    'Seafood': {
        'servers': 7,             # Không gian vật lý để đứng lấy thức ăn
        'capacity_K': 10,         # Tổng không gian vật lý (bao gồm cả không gian xếp hàng)
        'discipline': 'FCFS',     # FCFS
        'avg_service_time': 0.3
    },
    'Dessert': {
        'servers': 7,             # Không gian vật lý để đứng lấy thức ăn
        'capacity_K': 10,         # Tổng không gian vật lý (bao gồm cả không gian xếp hàng)
        'discipline': 'FCFS',     # FCFS
        'avg_service_time': 0.5
    },
    'Fruit': {
        'servers': 10,            # Không gian vật lý để đứng lấy thức ăn
        'capacity_K': 10,         # Tổng không gian vật lý (bao gồm cả không gian xếp hàng)
        'discipline': 'FCFS',     # FCFS
        'avg_service_time': 0.3
    }
}

# Ma trận xác suất
PROB_MATRICES = {
    # Xác suất chọn quầy ban đầu
    'initial': {
        # Cổng 0
        0: {
            'Meat': 0.4,
            'Seafood': 0.3,
            'Dessert': 0.2,
            'Fruit': 0.2
        },
        # Cổng 1
        1: {
            'Meat': 0.3,
            'Seafood': 0.4,
            'Dessert': 0.15,
            'Fruit': 0.15
        }
    },
    
    # Xác suất "Lấy thêm" hay "Về"
    'next_action': {
        'More': 0.7,  # 70% lấy thêm
        'Exit': 0.3   # 30% ra về
    },
    
    # Xác suất chọn quầy tiếp theo (nếu chọn 'More')
    'transition': {
        'Meat': 0.25,
        'Seafood': 0.25,
        'Dessert': 0.25,
        'Fruit': 0.25
    }
}

