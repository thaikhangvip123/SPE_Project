# main.py
import simpy
import config
from classes.buffet_system import BuffetSystem
from classes.analysis import Analysis

def run_simulation():
    """
    Thiết lập và chạy mô phỏng chính.
    """
    
    # 1. Khởi tạo môi trường
    env = simpy.Environment()
    
    # 2. Khởi tạo bộ phân tích
    analyzer = Analysis()
    
    # 3. Khởi tạo hệ thống buffet (truyền config vào)
    buffet = BuffetSystem(env, analyzer, config)
    
    # 4. Chạy mô phỏng
    buffet.run(until_time=config.UNTIL_TIME)
    
    # 5. Tính toán và in kết quả
    analyzer.calculate_statistics()
    analyzer.print_report()

if __name__ == "__main__":
    run_simulation()