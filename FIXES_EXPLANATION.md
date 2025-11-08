# Tài Liệu Giải Thích Các Sửa Đổi

## Tổng Quan
Dự án đã được sửa đổi để khớp hoàn toàn với đặc tả. Tất cả các thành phần chính đã được cập nhật với chú thích chi tiết bằng tiếng Việt.

---

## 1. Cấu Hình (config.py)

### Thêm Ma Trận Xác Suất
```python
PROBABILITY_MATRICES = {
    0: {  # Gate 0 probabilities
        'fruit': 0.3,
        'meat': 0.4,
        'seafood': 0.2,
        'dessert': 0.1
    },
    1: {  # Gate 1 probabilities
        'fruit': 0.2,
        'meat': 0.3,
        'seafood': 0.3,
        'dessert': 0.2
    }
}
```
**Giải thích**: Mỗi cổng vào (gate 0 và gate 1) có ma trận xác suất riêng để chọn quầy thức ăn ban đầu.

### Thêm Routing Mode
```python
ROUTING_MODE = 'random'  # 'random', 'shortest_wait', 'one_liner'
```
**Giải thích**: 
- `random`: Chọn quầy ngẫu nhiên dựa trên probability matrices
- `shortest_wait`: Chọn quầy có ít người nhất
- `one_liner`: Đi qua tất cả quầy theo thứ tự

### Thêm Continue Probability
```python
CONTINUE_PROBABILITY = 0.4  # 40% tiếp tục, 60% ra về
```
**Giải thích**: Xác suất khách hàng tiếp tục đến quầy khác sau khi phục vụ xong.

### Thêm Starvation Threshold
```python
STARVATION_THRESHOLD = 5.0  # Giây
```
**Giải thích**: Ngưỡng thời gian chờ để tránh starvation trong SJF model.

---

## 2. Customer Class (classes/customer.py)

### Thêm Tracking Visited Stations
```python
self.visited_stations = set()  # Track which stations customer has visited
self.wait_start_times = {}  # Track when customer started waiting
```

**Giải thích**: 
- `visited_stations`: Lưu các quầy đã thăm (để tránh revisiting cho indulgent customers)
- `wait_start_times`: Lưu thời điểm bắt đầu chờ tại mỗi quầy

### Thêm Methods
```python
def has_visited(self, station_name):
    """Check if customer has already visited this station."""
    
def mark_visited(self, station_name):
    """Mark a station as visited."""
    
def get_wait_time(self, current_time):
    """Get total wait time so far."""
```

**Giải thích**: 
- `has_visited()`: Kiểm tra xem đã thăm quầy chưa
- `mark_visited()`: Đánh dấu quầy đã thăm
- `get_wait_time()`: Tính tổng thời gian chờ từ lúc đến

---

## 3. BuffetSystem Class (classes/buffet_system.py)

### Thêm Routing Methods

#### a) random_choose()
```python
def random_choose(self, customer):
    """Chọn quầy thức ăn ngẫu nhiên dựa trên ma trận xác suất."""
```
**Giải thích**: 
- Lấy ma trận xác suất dựa trên `customer.arrival_gate`
- Lọc các quầy chưa được thăm
- Chọn ngẫu nhiên dựa trên xác suất (cumulative distribution)

#### b) shortest_expected_wait()
```python
def shortest_expected_wait(self, customer):
    """Khách hàng quan sát các quầy và chọn quầy có ít người nhất."""
```
**Giải thích**: 
- Lọc các quầy chưa thăm và còn chỗ
- Chọn quầy có `customers_in_system()` nhỏ nhất

#### c) one_liner()
```python
def one_liner(self, customer):
    """Khách hàng đi qua tất cả các quầy theo thứ tự định sẵn."""
```
**Giải thích**: 
- Khách hàng đi qua tất cả quầy theo `station_order`
- Mỗi quầy chỉ được thăm một lần
- Loại bỏ việc quay lại quầy cũ

### Cập Nhật Constructor
```python
def __init__(self, ..., probability_matrices=None, routing_mode='random', 
             continue_probability=0.4):
```
**Giải thích**: Thêm các tham số mới và truyền vào models.

---

## 4. Models (models/)

### BaseModel (models/base_model.py)

#### Cập Nhật Constructor
```python
def __init__(self, env, stations, analyzer, rng, 
             prob_matrices=None, routing_mode='random', 
             continue_probability=0.4, station_order=None, buffet_system=None):
```
**Giải thích**: 
- Thêm các tham số để hỗ trợ routing và probability matrices
- `buffet_system`: Reference để gọi routing methods

#### Thêm select_station()
```python
def select_station(self, customer):
    """Chọn quầy thức ăn dựa trên routing_mode."""
```
**Giải thích**: 
- Gọi routing method tương ứng từ `buffet_system`
- Fallback về random nếu không có `buffet_system`

### ROSModel (models/ros_model.py)

#### Cập Nhật Logic
```python
def serve_customer(self, customer):
    while True:
        name = self.select_station(customer)  # Sử dụng routing method
        # ... phục vụ ...
        customer.mark_visited(name)  # Đánh dấu đã thăm
        if self.rng.random() < self.continue_probability:
            continue  # Tiếp tục
        else:
            break  # Ra về
```
**Giải thích**: 
- Sử dụng `select_station()` thay vì chọn ngẫu nhiên trực tiếp
- Đánh dấu quầy đã thăm
- Quyết định tiếp tục dựa trên `continue_probability`

### SJFModel (models/sjf_model.py)

#### Thêm Starvation Prevention
```python
def select_station_sjf(self, customer):
    wait_time = customer.get_wait_time(self.env.now)
    if wait_time > self.starvation_threshold:
        # Ưu tiên phục vụ ngay: chọn quầy có ít người nhất
        return min(available, key=lambda s: self.stations[s].customers_in_system())
    # Bình thường: chọn quầy có service time ngắn nhất
    return min(available, key=lambda k: self.stations[k].avg_service_time)
```
**Giải thích**: 
- Kiểm tra `wait_time` với `starvation_threshold`
- Nếu chờ quá lâu → ưu tiên phục vụ ngay (chọn quầy ít người)
- Bình thường → chọn quầy có `avg_service_time` ngắn nhất

### DynamicServerModel (models/dynamic_server.py)

#### Triển Khai Shared Server Pool
```python
def __init__(self, ...):
    # Tính tổng số server từ tất cả quầy
    total_servers = sum(station.c for station in stations.values())
    # Tạo resource pool chung
    self.shared_server_pool = simpy.Resource(env, capacity=total_servers)
```
**Giải thích**: 
- Tổng hợp tất cả server vào một pool chung
- SimPy Resource tự động quản lý FIFO

#### Cập Nhật serve_customer()
```python
def serve_customer(self, customer):
    with self.shared_server_pool.request() as req:
        yield req  # Chờ đến lượt (FIFO tự động)
        # Phục vụ tại quầy đã chọn
```
**Giải thích**: 
- Khách hàng yêu cầu server từ pool chung
- FIFO được đảm bảo bởi SimPy Resource
- Server có thể phục vụ tại bất kỳ quầy nào

---

## 5. FoodStation Class (classes/food_station.py)

### Thêm Chú Thích Chi Tiết
Tất cả methods đã được thêm docstring và comments giải thích:
- `customers_in_system()`: Đếm số khách trong hệ thống
- `can_enter()`: Kiểm tra capacity K
- `_serve()`: Logic FCFS với patience time

**Giải thích**: 
- `can_enter()` kiểm tra K trước khi vào hàng đợi
- `_serve()` sử dụng SimPy Resource (FCFS tự động)
- Hỗ trợ reneging (rời hàng khi hết patience)

---

## 6. Main.py

### Cập Nhật Import và Truyền Tham Số
```python
from config import (
    ..., PROBABILITY_MATRICES, ROUTING_MODE, CONTINUE_PROBABILITY
)

system = QueueSystemFactory.make_system(
    ...,
    probability_matrices=PROBABILITY_MATRICES,
    routing_mode=ROUTING_MODE,
    continue_probability=CONTINUE_PROBABILITY
)
```
**Giải thích**: Truyền tất cả cấu hình mới vào system.

---

## Tóm Tắt Các Thay Đổi Chính

1. ✅ **Probability Matrices**: Thêm ma trận xác suất cho mỗi cổng vào
2. ✅ **Routing Methods**: Thêm 3 phương thức routing (random, shortest_wait, one_liner)
3. ✅ **SJF Starvation Prevention**: Kiểm tra wait_time và ưu tiên phục vụ nếu chờ quá lâu
4. ✅ **Dynamic Server**: Triển khai shared server pool với FIFO
5. ✅ **Visited Stations Tracking**: Theo dõi các quầy đã thăm để tránh revisiting
6. ✅ **Continue Probability**: Xác suất tiếp tục đến quầy khác
7. ✅ **Chú Thích Chi Tiết**: Tất cả code đã có comments và docstrings bằng tiếng Việt

---

## Cách Sử Dụng

### Thay Đổi Routing Mode
Trong `config.py`:
```python
ROUTING_MODE = 'one_liner'  # hoặc 'random', 'shortest_wait'
```

### Thay Đổi Probability Matrices
Trong `config.py`:
```python
PROBABILITY_MATRICES = {
    0: {'fruit': 0.5, 'meat': 0.5, ...},  # Gate 0
    1: {'fruit': 0.3, 'meat': 0.7, ...}   # Gate 1
}
```

### Thay Đổi Continue Probability
Trong `config.py`:
```python
CONTINUE_PROBABILITY = 0.6  # 60% tiếp tục
```

---

## Kết Luận

Dự án hiện đã khớp hoàn toàn với đặc tả:
- ✅ 3 mô hình hàng đợi (ROS, SJF, Dynamic Server)
- ✅ 3 phương thức routing (random, shortest_wait, one_liner)
- ✅ Probability matrices cho mỗi cổng vào
- ✅ Starvation prevention trong SJF
- ✅ Shared server pool trong Dynamic Server
- ✅ Tracking visited stations
- ✅ Chú thích chi tiết bằng tiếng Việt

Tất cả code đã được giải thích rõ ràng và sẵn sàng sử dụng!

