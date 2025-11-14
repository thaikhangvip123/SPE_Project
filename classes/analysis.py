# classes/analysis.py
import numpy as np

class Analysis:
    """
    Tách biệt logic thu thập và xử lý số liệu ra khỏi mô phỏng. 
    """
    def __init__(self):
        # --- Bộ đếm (Counters) ---
        self.total_arrivals = 0      # [cite: 163]
        self.total_exits = 0         # [cite: 164]
        
        # Khách bỏ đi vì không gian K đầy (Balking) [cite: 166, 222]
        self.total_balked = 0        
        
        # Khách bỏ đi vì chờ quá lâu (Reneging) 
        self.total_reneged = 0       
        
        # --- Dữ liệu thô (Raw Data) ---
        # {'Meat': [t1, t2], 'Seafood': [t3, ...]}
        self.wait_times = {}         # [cite: 167]
        self.system_times = []       # List thời gian khách ở trong hệ thống [cite: 168]
        
        # {'Meat': 5, 'Seafood': 2} (số lần bị chặn)
        self.blocking_events = {}    # [cite: 169]
        
        # --- Thống kê đã tính (Calculated Statistics) ---
        self.avg_wait_time_per_station = {}
        self.avg_system_time = 0.0
        self.blocking_probability_per_station = {}
        self.total_attempts_per_station = {} # Cần để tính xác suất

    def add_station(self, station_name):
        """Đăng ký station để theo dõi số liệu."""
        if station_name not in self.wait_times:
            self.wait_times[station_name] = []
            self.blocking_events[station_name] = 0
            self.total_attempts_per_station[station_name] = 0

    def record_arrival(self):
        """[cite: 171]"""
        self.total_arrivals += 1

    def record_exit(self, system_time):
        """[cite: 172]"""
        self.total_exits += 1
        self.system_times.append(system_time)

    def record_attempt(self, station_name):
        """Ghi nhận khi khách *cố gắng* vào một quầy."""
        self.total_attempts_per_station[station_name] += 1

    def record_wait_time(self, station_name, wait):
        """[cite: 173]"""
        self.wait_times[station_name].append(wait)

    def record_blocking_event(self, station_name):
        """Ghi nhận khi khách bị chặn (Balking)[cite: 174, 222]."""
        self.blocking_events[station_name] += 1
        self.total_balked += 1

    def record_reneging_event(self):
        """Ghi nhận khi khách rời hàng đợi (Reneging)."""
        self.total_reneged += 1

    def calculate_statistics(self):
        """
        Tính toán các chỉ số có ý nghĩa từ dữ liệu thô. [cite: 248, 249]
        """
        if self.system_times:
            self.avg_system_time = np.mean(self.system_times)
        else:
            self.avg_system_time = 0.0

        for station, times in self.wait_times.items():
            if times:
                self.avg_wait_time_per_station[station] = np.mean(times)
            else:
                self.avg_wait_time_per_station[station] = 0.0
        
        for station, blocked_count in self.blocking_events.items():
            attempts = self.total_attempts_per_station.get(station, 0)
            if attempts > 0:
                self.blocking_probability_per_station[station] = blocked_count / attempts
            else:
                self.blocking_probability_per_station[station] = 0.0

    def print_report(self):
        """Định dạng và in kết quả đã tính. """
        print("--- BAO CAO MO PHONG ---")
        print(f"Tong so khach den: {self.total_arrivals}")
        print(f"Tong so khach thoat: {self.total_exits}")
        print(f"Tong so khach bo ve (Balked - het cho K): {self.total_balked}")
        print(f"Tong so khach bo ve (Reneged - mat kien nhan): {self.total_reneged}")
        
        print(f"\nThoi gian trung binh trong he thong: {self.avg_system_time:.2f}")
        
        print("\nThoi gian cho trung binh tai quay:")
        for station, time in self.avg_wait_time_per_station.items():
            print(f"  - {station:<10}: {time:.2f}")

        print("\nXac suat bi chan (Balking):")
        for station, prob in self.blocking_probability_per_station.items():
            print(f"  - {station:<10}: {prob:.2%}")