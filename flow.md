# Tài liệu giải thích luồng hoạt động hệ thống mô phỏng Buffet

## 1. Tổng quan hệ thống

Hệ thống mô phỏng một nhà hàng buffet với nhiều quầy thức ăn (Food Stations). Khách hàng đến từ 2 cổng khác nhau, di chuyển qua các quầy để lấy thức ăn, và có thể rời đi nếu chờ quá lâu.

### Các thành phần chính:

- **BuffetSystem** (Hệ thống Buffet): Quản lý toàn bộ hệ thống, điều khiển luồng khách hàng và routing giữa các quầy
- **FoodStation** (Quầy thức ăn): Đại diện cho một quầy thức ăn, mô hình hóa hàng đợi M/M/c/K
- **Customer** (Khách hàng): Đại diện cho một khách hàng trong hệ thống
- **Queue Models** (Mô hình hàng đợi): Các mô hình kỷ luật hàng đợi (FCFS, SJF, ROS)
- **Analysis** (Phân tích): Thu thập và phân tích dữ liệu từ mô phỏng

### Thuật ngữ quan trọng:

- **M/M/c/K Queue**: Mô hình hàng đợi với:
  - **M** (Markovian): Phân phối exponential cho thời gian đến và phục vụ
  - **c**: Số lượng server (người phục vụ/kẹp gắp)
  - **K**: Khả năng chứa tối đa (capacity - sức chứa)
- **FCFS** (First Come First Served): Ai đến trước phục vụ trước
- **SJF** (Shortest Job First): Ưu tiên khách có thời gian phục vụ ngắn nhất
- **ROS** (Random Order Serving): Phục vụ ngẫu nhiên
- **Balking**: Khách bỏ đi vì không có chỗ (hết capacity K)
- **Reneging**: Khách bỏ đi vì chờ quá lâu (hết kiên nhẫn - patience)
- **Patience Time**: Thời gian kiên nhẫn tối đa khách sẵn sàng chờ
- **Service Time**: Thời gian phục vụ (lấy thức ăn)
- **Wait Time**: Thời gian chờ trong hàng đợi
- **System Time**: Tổng thời gian khách ở trong hệ thống

---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────┐
│                    main.py                              │
│  - Khởi tạo SimPy Environment (Môi trường SimPy)        │
│  - Tạo BuffetSystem và Analysis                         │
│  - Chạy mô phỏng                                        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                BuffetSystem                              │
│  - Quản lý các FoodStation                               │
│  - Tạo khách hàng (generate_customers)                  │
│  - Điều khiển hành trình khách (customer_lifecycle)      │
│  - Quyết định routing (định tuyến) giữa các station     │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ FoodStation  │    │ FoodStation  │    │ FoodStation  │
│   (Meat)     │    │  (Seafood)   │    │  (Dessert)   │
└──────────────┘    └──────────────┘    └──────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Queue Model  │    │ Queue Model  │    │ Queue Model  │
│   (FCFS)     │    │   (SJF)      │    │   (ROS)      │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 3. Luồng hoạt động chính

### 3.1. Khởi tạo hệ thống (System Initialization)

```
1. main.py tạo SimPy Environment (Môi trường SimPy)
   - Environment: Môi trường mô phỏng sự kiện rời rạc (discrete-event simulation)
   
2. Tạo Analysis object để thu thập dữ liệu
   - Analysis: Bộ phân tích thu thập và tính toán thống kê
   
3. Tạo BuffetSystem:
   - Đọc config (STATIONS, ARRIVAL_RATES, PROB_MATRICES)
     * STATIONS: Cấu hình các quầy thức ăn
     * ARRIVAL_RATES: Tốc độ khách đến từ mỗi cổng
     * PROB_MATRICES: Ma trận xác suất routing
   - Dùng QueueSystemFactory (Nhà máy tạo mô hình hàng đợi) tạo queue model cho mỗi station
   - Tạo FoodStation cho mỗi quầy với model tương ứng
   
4. Khởi chạy các process (tiến trình) generate_customers cho mỗi cổng
   - Process: Tiến trình chạy song song trong SimPy
   
5. Chạy mô phỏng đến thời gian UNTIL_TIME
```

### 3.2. Tạo khách hàng (Customer Generation - generate_customers)

**Luồng:**
```
For mỗi cổng (gate_id):
  While True:
    1. Tính inter_arrival_time (thời gian giữa các lần đến) 
       theo phân phối exponential (phân phối mũ)
       - Rate (tốc độ) = ARRIVAL_RATES[gate_id]
       - Exponential: Phân phối xác suất mô tả thời gian giữa các sự kiện
       
    2. Chờ inter_arrival_time
       - yield env.timeout(inter_arrival_time)
       
    3. Tạo Customer mới:
       - ID = total_arrivals (tổng số khách đã đến)
       - arrival_gate = gate_id (cổng vào)
       - arrival_time = env.now (thời điểm hiện tại)
       - patience_time = DEFAULT_PATIENCE_TIME (15 phút)
       - service_times = random cho mỗi station (thời gian phục vụ ngẫu nhiên)
         * Mỗi khách có service_time riêng cho từng quầy
         * Dao động 50%-150% so với thời gian trung bình
         
    4. Ghi nhận arrival (sự kiện đến)
       - analyzer.record_arrival()
       
    5. Khởi chạy customer_lifecycle process (tiến trình hành trình khách)
       - env.process(customer_lifecycle(new_customer))
```

**Đặc điểm:**
- Mỗi cổng có một process riêng chạy song song (parallel)
- Phân phối Poisson (exponential inter-arrival)
  - Poisson: Mô tả số lượng sự kiện xảy ra trong khoảng thời gian
  - Exponential: Mô tả thời gian giữa các sự kiện
- Service times được tạo ngẫu nhiên cho mỗi khách (50%-150% của base time)

---

## 4. Luồng hành trình khách hàng (Customer Lifecycle - customer_lifecycle)

### 4.1. Sơ đồ tổng quan

```
Khách hàng đến (Customer Arrives)
    │
    ▼
Chọn quầy đầu tiên (choose_initial_section)
    │
    ▼
┌─────────────────────────────────────┐
│  WHILE (còn quầy để đi):            │
│    1. Đến quầy (station.serve)      │
│       - Chờ không gian K (Balking) │
│       - Chờ server (Reneging)      │
│       - Được phục vụ                │
│    2. Kiểm tra reneged?              │
│       - Nếu có: BREAK (dừng lại)    │
│    3. Chọn hành động tiếp theo       │
│       (choose_next_action)           │
│       - Exit: station_name = None    │
│       - More: chọn quầy tiếp theo   │
└─────────────────────────────────────┘
    │
    ▼
Ghi nhận exit (thoát) và system_time (thời gian trong hệ thống)
```

### 4.2. Chi tiết từng bước

#### Bước 1: Chọn quầy đầu tiên (Initial Station Selection)

```python
choose_initial_section(gate_id):
  - Lấy ma trận xác suất từ PROB_MATRICES['initial'][gate_id]
    * Probability Matrix: Ma trận xác suất
  - Chọn ngẫu nhiên dựa trên trọng số xác suất (weighted random)
    * Weight: Trọng số, xác suất tương ứng
  - Ví dụ: Gate 0 → Meat(0.4), Seafood(0.3), Dessert(0.2), Fruit(0.2)
```

#### Bước 2: Phục vụ tại quầy (Station Service - station.serve)

Xem chi tiết ở phần 5.

#### Bước 3: Chọn hành động tiếp theo (Next Action Selection)

```python
choose_next_action(customer, visited_stations):
  1. Quyết định: More (70%) hay Exit (30%)
     - More: Lấy thêm thức ăn
     - Exit: Ra về
     
  2. Nếu Exit → return None (kết thúc hành trình)
  
  3. Nếu More:
     - Lọc các quầy chưa thăm (chưa visited)
     - Chọn ngẫu nhiên từ các quầy còn lại
     - Nếu không còn quầy → return None
```

---

## 5. Luồng xử lý tại FoodStation (station.serve)

### 5.1. Sơ đồ chi tiết

```
Khách đến FoodStation (Customer arrives at FoodStation)
    │
    ▼
Ghi nhận attempt (ghi nhận lần cố gắng vào quầy)
    │
    ▼
┌─────────────────────────────────────┐
│  BƯỚC 1: Chờ không gian K (Balking) │
│  - Yêu cầu 1 slot từ queue_space     │
│    * queue_space: Không gian hàng đợi (Container trong SimPy)
│  - Set start_wait_time = env.now    │
│    * start_wait_time: Thời điểm bắt đầu chờ
│  - Timeout = patience_time           │
│    * Timeout: Hết thời gian chờ      │
│                                       │
│  Nếu timeout (hết thời gian chờ):   │
│    → customer.reneged = True          │
│      * reneged: Đã rời đi            │
│    → record_blocking_event            │
│      * Blocking: Bị chặn             │
│    → RETURN (khách rời đi)           │
└─────────────────────────────────────┘
    │
    ▼ (Đã có chỗ K - có không gian)
┌─────────────────────────────────────┐
│  BƯỚC 2: Chờ server (Reneging)      │
│  - Ủy quyền cho discipline_model     │
│    * discipline_model: Mô hình kỷ luật hàng đợi
│    (FCFS/SJF/ROS)                    │
│  - Xử lý logic chờ server            │
│    * Server: Người phục vụ/kẹp gắp   │
└─────────────────────────────────────┘
    │
    ▼ (Đã được phục vụ hoặc reneged)
┌─────────────────────────────────────┐
│  BƯỚC 3: Trả lại không gian K       │
│  - queue_space.put(1)               │
│    * Giải phóng 1 slot không gian    │
└─────────────────────────────────────┘
```

### 5.2. Mô hình hàng đợi M/M/c/K

- **M** (Markovian): Phân phối exponential cho inter-arrival (thời gian đến)
- **M** (Markovian): Phân phối exponential cho service time (thời gian phục vụ)
- **c**: Số lượng server (người phục vụ/kẹp gắp)
- **K**: Khả năng chứa tối đa (capacity_K - sức chứa)

**Hai tầng chờ (Two-tier waiting):**
1. **Tầng K (Balking)**: Chờ không gian vật lý trong quầy
   - Capacity K: Sức chứa tối đa của quầy
   - Nếu đầy, khách phải chờ hoặc bỏ đi
2. **Tầng c (Reneging)**: Chờ server rảnh để phục vụ
   - Server: Người phục vụ (tongs, ladles)
   - Nếu tất cả server đều bận, khách phải chờ

---

## 6. Luồng xử lý trong Queue Models (FCFS)

### 6.1. FCFS Model Flow (Luồng mô hình FCFS)

```
Khách vào serve() của FCFS
    │
    ▼
Tính patience_remaining (thời gian kiên nhẫn còn lại):
  = patience_time - time_spent_waiting_K
    * time_spent_waiting_K: Thời gian đã chờ để có không gian K
    │
    ▼
Nếu patience_remaining <= 0:
  → customer.reneged = True
  → record_reneging_event (ghi nhận sự kiện reneging)
  → RETURN
    │
    ▼
Yêu cầu server (servers.request())
    * request(): Yêu cầu tài nguyên server
    │
    ▼
Chờ: req | timeout(patience_remaining)
    * req: Yêu cầu server
    * timeout: Hết thời gian chờ
    │
    ├─ Timeout trước (hết kiên nhẫn)
    │  → customer.reneged = True
    │  → record_reneging_event
    │  → RETURN
    │
    └─ Được server (req trong results)
       │
       ▼
   Ghi nhận wait_time (thời gian chờ)
       │
       ▼
   Tính actual_service_time (thời gian phục vụ thực tế):
     = expovariate(1.0 / base_service_time)
       * expovariate: Sinh số ngẫu nhiên theo phân phối exponential
       * base_service_time: Thời gian phục vụ cơ bản
       │
       ▼
   Chờ service_time (thời gian phục vụ)
       │
       ▼
   Hoàn thành (server tự động được giải phóng)
       * Server được trả lại pool (nhóm server)
```

### 6.2. Các mô hình khác

**SJF (Shortest Job First - Công việc ngắn nhất trước):**
- Dùng priority queue (hàng đợi ưu tiên - heapq)
- Ưu tiên khách có service_time ngắn nhất
- Có logic chống starvation (chống đói)
  - Starvation: Hiện tượng một số khách bị chờ quá lâu
  - Threshold: Ngưỡng thời gian chờ để kích hoạt ưu tiên

**ROS (Random Order Serving - Phục vụ thứ tự ngẫu nhiên):**
- Chọn khách ngẫu nhiên từ hàng đợi
- Dùng list Python đơn giản
- Fair: Công bằng cho tất cả khách

---

## 7. Logic Reneging và Balking

### 7.1. Balking (Chặn do hết chỗ K)

**Balking**: Khách bỏ đi vì không có chỗ (không gian K đầy)

**Xảy ra khi:**
- Khách không thể vào quầy vì `queue_space` đầy
  - queue_space: Không gian hàng đợi (Container trong SimPy)
- Chờ quá `patience_time` mà vẫn không có chỗ

**Xử lý:**
```python
# Trong food_station.py
results = yield get_space_req | env.timeout(customer.patience_time)
# get_space_req: Yêu cầu lấy không gian
# | : Toán tử OR trong SimPy (chờ một trong hai sự kiện)
# timeout: Hết thời gian chờ

if get_space_req not in results:
    # get_space_req không có trong results → timeout xảy ra trước
    customer.reneged = True
    analyzer.record_blocking_event(station_name)
    # record_blocking_event: Ghi nhận sự kiện bị chặn
    return
```

### 7.2. Reneging (Rời đi do mất kiên nhẫn)

**Reneging**: Khách rời hàng đợi vì chờ quá lâu (hết kiên nhẫn)

**Xảy ra khi:**
- Khách đã vào quầy (có chỗ K) nhưng chờ server quá lâu
- Thời gian chờ vượt quá `patience_remaining` (thời gian kiên nhẫn còn lại)

**Xử lý:**
```python
# Trong fcfs.py (và các model khác)
time_spent_waiting_K = env.now - customer.start_wait_time
# Tính thời gian đã chờ để có không gian K

patience_remaining = patience_time - time_spent_waiting_K
# Tính thời gian kiên nhẫn còn lại

results = yield req | env.timeout(patience_remaining)
# Chờ: được server HOẶC hết thời gian kiên nhẫn

if req not in results:
    # req không có trong results → timeout xảy ra trước
    customer.reneged = True
    analyzer.record_reneging_event()
    # record_reneging_event: Ghi nhận sự kiện reneging
    return
```

**Lưu ý quan trọng:**
- `patience_time` được dùng lại cho mỗi station (mỗi quầy)
- Thời gian chờ K được trừ vào `patience_remaining` khi chờ server
- Nếu khách đã chờ K gần hết `patience_time`, sẽ có rất ít thời gian chờ server

---

## 8. Thu thập và phân tích dữ liệu (Data Collection and Analysis)

### 8.1. Các sự kiện được ghi nhận

**Analysis class thu thập:**
- `total_arrivals`: Tổng số khách đến
- `total_exits`: Tổng số khách thoát
- `total_balked`: Số khách bị chặn (Balking)
- `total_reneged`: Số khách rời đi (Reneging)
- `wait_times[station]`: Thời gian chờ tại mỗi station
  - Dictionary lưu danh sách thời gian chờ
- `system_times`: Thời gian trong hệ thống
  - List lưu tổng thời gian mỗi khách ở trong hệ thống
- `blocking_events[station]`: Số lần bị chặn tại mỗi station
- `total_attempts_per_station[station]`: Tổng số lần cố gắng vào mỗi station

### 8.2. Các chỉ số được tính (Calculated Statistics)

- **Thời gian chờ trung bình** tại mỗi station (Average Wait Time)
  - Tính bằng mean (trung bình) của wait_times[station]
- **Thời gian trong hệ thống trung bình** (Average System Time)
  - Tính bằng mean của system_times
- **Xác suất bị chặn** (Blocking Probability) tại mỗi station
  - = blocking_events[station] / total_attempts_per_station[station]

---

## 9. Ví dụ luồng hoạt động chi tiết

### Scenario 1: Khách hàng đi qua 2 quầy (bình thường)

```
Time = 0.0: Khách #100 đến từ Gate 0
  → choose_initial_section(0) → Chọn "Meat" (40% xác suất)
  
Time = 0.0: Đến Meat Station
  → food_station.serve(customer_100)
    → Chờ K: queue_space.get(1)
      * get(1): Lấy 1 slot không gian
    → Có chỗ ngay (queue_space có sẵn)
    → start_wait_time = 0.0
    
    → fcfs.serve(customer_100)
      → time_spent_waiting_K = 0.0 - 0.0 = 0.0
      → patience_remaining = 15.0 - 0.0 = 15.0
      → Yêu cầu server (10 servers có sẵn)
      → Được server ngay
      → base_service_time = 2.0 (từ customer.service_times['Meat'])
      → actual_service_time = expovariate(1.0/2.0) = 1.5 phút
      → Chờ 1.5 phút (service time)
      
Time = 1.5: Hoàn thành Meat
  → Trả lại queue_space (put(1))
  → customer.reneged = False (vẫn OK)
  
Time = 1.5: choose_next_action
  → 70% More, 30% Exit → Chọn "More" (lấy thêm)
  → Chọn "Seafood" (chưa thăm, từ transition matrix)
  
Time = 1.5: Đến Seafood Station
  → food_station.serve(customer_100)
    → Chờ K: queue_space.get(1)
    → Có chỗ ngay
    → start_wait_time = 1.5 (reset cho station mới)
    
    → fcfs.serve(customer_100)
      → time_spent_waiting_K = 1.5 - 1.5 = 0.0
      → patience_remaining = 15.0 - 0.0 = 15.0
        (Lưu ý: patience_time được reset cho mỗi station)
      → Yêu cầu server (5 servers, đang bận)
      → Chờ server...
      → Được server sau 2.0 phút
      → service_time = expovariate(1.0/3.0) = 2.5 phút
      → Chờ 2.5 phút
      
Time = 6.0: Hoàn thành Seafood
  → Trả lại queue_space
  → customer.reneged = False
  
Time = 6.0: choose_next_action
  → Chọn "Exit" (30% xác suất)
  → station_name = None
  
Time = 6.0: Rời hệ thống
  → system_time = 6.0 - 0.0 = 6.0 phút
  → record_exit(6.0)
```

### Scenario 2: Khách hàng bị Reneging (hết kiên nhẫn)

```
Time = 10.0: Khách #200 đến từ Gate 1
  → Chọn "Seafood" (40% xác suất)
  
Time = 10.0: Đến Seafood Station
  → Chờ K: Có chỗ ngay
  → start_wait_time = 10.0
  
  → fcfs.serve(customer_200)
    → time_spent_waiting_K = 10.0 - 10.0 = 0.0
    → patience_remaining = 15.0
    → Yêu cầu server (5 servers đều bận)
    → Chờ server...
    → Chờ 14.5 phút vẫn chưa có server
    → Timeout! (patience_remaining = 0.5 < 14.5)
      * Hết thời gian kiên nhẫn trước khi được server
    
Time = 24.5: Hết kiên nhẫn
  → customer.reneged = True
  → record_reneging_event()
  → RETURN (không được phục vụ)
  
Time = 24.5: customer_lifecycle kiểm tra
  → if customer.reneged: BREAK
  → Không đi đến station khác
  
Time = 24.5: Rời hệ thống
  → system_time = 24.5 - 10.0 = 14.5 phút
  → record_exit(14.5)
```

### Scenario 3: Khách hàng bị Balking (hết chỗ K)

```
Time = 50.0: Khách #300 đến từ Gate 0
  → Chọn "Seafood" (30% xác suất)
  
Time = 50.0: Đến Seafood Station
  → food_station.serve(customer_300)
    → Chờ K: queue_space.get(1)
    → queue_space đầy (capacity_K = 10, đã có 10 khách)
    → Chờ không gian...
    → Chờ 15.0 phút (patience_time) vẫn không có chỗ
    → Timeout!
    
Time = 65.0: Hết kiên nhẫn khi chờ K
  → customer.reneged = True
  → record_blocking_event('Seafood')
  → RETURN (không vào được quầy)
  
Time = 65.0: customer_lifecycle kiểm tra
  → if customer.reneged: BREAK
  → Không đi đến station khác
  
Time = 65.0: Rời hệ thống
  → system_time = 65.0 - 50.0 = 15.0 phút
  → record_exit(15.0)
```

---

## 10. Cấu hình hệ thống (System Configuration)

### 10.1. Các tham số chính (config.py)

- **UNTIL_TIME**: Thời gian mô phỏng (1000 phút)
- **ARRIVAL_RATES**: Tốc độ đến từ mỗi cổng (arrival rate - tỷ lệ đến)
  - Gate 0: 1.0 khách/phút
  - Gate 1: 1.0 khách/phút
- **DEFAULT_PATIENCE_TIME**: 15 phút (thời gian kiên nhẫn mặc định)
- **STATIONS**: Cấu hình mỗi quầy
  - `servers`: Số lượng server (người phục vụ)
  - `capacity_K`: Khả năng chứa (sức chứa)
  - `discipline`: Mô hình hàng đợi (FCFS/SJF/ROS)
  - `avg_service_time`: Thời gian phục vụ trung bình
- **PROB_MATRICES**: Ma trận xác suất routing (định tuyến)
  - `initial`: Xác suất chọn quầy đầu tiên
  - `next_action`: Xác suất "More" hay "Exit"
  - `transition`: Xác suất chọn quầy tiếp theo

### 10.2. Factory Pattern (Mẫu thiết kế Nhà máy)

`QueueSystemFactory` (Nhà máy tạo mô hình hàng đợi) tạo queue model dựa trên `discipline`:
- 'FCFS' → FCFSModel
- 'SJF' → SJFModel  
- 'ROS' → ROSModel

**Factory Pattern**: Mẫu thiết kế tạo đối tượng mà không cần chỉ định chính xác class nào sẽ được tạo

---

## 11. Điểm quan trọng cần lưu ý

### 11.1. Patience Time (Thời gian kiên nhẫn)

- **Mỗi station dùng lại toàn bộ `patience_time`**
  - Khi khách vào station mới, `patience_time` được reset về giá trị ban đầu (15 phút)
  - `start_wait_time` được set lại = `env.now` khi vào station mới
- Thời gian chờ K được trừ vào `patience_remaining` khi chờ server
  - `patience_remaining = patience_time - time_spent_waiting_K`
  - `time_spent_waiting_K = env.now - customer.start_wait_time`
- Nếu khách chờ K lâu, sẽ có ít thời gian chờ server
  - Ví dụ: Chờ K 14 phút → chỉ còn 1 phút để chờ server

### 11.2. Reneged Flag (Cờ đánh dấu rời đi)

- Được set = `True` khi khách bị Balking hoặc Reneging
- `customer_lifecycle` kiểm tra flag này để dừng hành trình
- Nếu không set đúng, khách có thể tiếp tục đi qua các station khác (lỗi logic)
- **Quan trọng**: Phải set `customer.reneged = True` ở cả:
  - `food_station.py`: Khi bị Balking (hết chỗ K)
  - `fcfs.py`, `sjf.py`, `ros.py`: Khi bị Reneging (hết kiên nhẫn khi chờ server)

### 11.3. Dependency Injection (Tiêm phụ thuộc)

- `FoodStation` nhận `discipline_model` từ bên ngoài (BuffetSystem)
- Cho phép dễ dàng thay đổi mô hình hàng đợi mà không sửa code FoodStation
- Tuân thủ nguyên tắc Open/Closed (mở để mở rộng, đóng để sửa đổi)
- Factory Pattern tạo model phù hợp dựa trên config

### 11.4. SimPy Events và Processes

- **Event**: Sự kiện trong SimPy (có thể chờ, trigger, succeed)
- **Process**: Tiến trình chạy song song (generator function với yield)
- **Resource**: Tài nguyên có giới hạn (servers)
- **Container**: Tài nguyên có thể lấy/trả (queue_space)
- **timeout**: Sự kiện tự động trigger sau một khoảng thời gian
- **| (OR)**: Toán tử chờ một trong hai sự kiện xảy ra trước

---

## 12. Kết luận

Hệ thống mô phỏng buffet này sử dụng:

- **SimPy** (Simulation in Python): Framework mô phỏng sự kiện rời rạc (discrete-event simulation)
- **Factory Pattern** (Mẫu thiết kế Nhà máy): Cho việc tạo queue models
- **Dependency Injection** (Tiêm phụ thuộc): Cho việc tiêm models vào stations
- **M/M/c/K queue model**: Mô hình hàng đợi với 2 tầng chờ (K và c)
- **Reneging và Balking**: Để mô phỏng hành vi thực tế của khách hàng

### Luồng hoạt động chính:

1. **Khách đến** theo phân phối Poisson (exponential inter-arrival)
2. **Chọn quầy** dựa trên xác suất (probability matrix)
3. **Chờ không gian K** (Balking) - nếu hết chỗ, khách bỏ đi
4. **Chờ server** (Reneging) - nếu chờ quá lâu, khách bỏ đi
5. **Được phục vụ** - lấy thức ăn (service time)
6. **Quyết định đi tiếp hay về** - dựa trên xác suất
7. **Lặp lại** cho đến khi Exit hoặc Reneged

### Các chỉ số hiệu suất (Performance Metrics):

- **Average Wait Time**: Thời gian chờ trung bình tại mỗi station
- **Average System Time**: Thời gian trung bình trong hệ thống
- **Blocking Probability**: Xác suất bị chặn (Balking)
- **Reneging Rate**: Tỷ lệ khách rời đi (Reneging)
- **Throughput**: Số khách được phục vụ thành công

### Cải thiện hệ thống:

- Tăng số server (`servers`) để giảm thời gian chờ
- Tăng capacity K để giảm Balking
- Tăng patience_time để giảm Reneging
- Điều chỉnh arrival rates để cân bằng tải
- Tối ưu routing probabilities để phân bố đều tải