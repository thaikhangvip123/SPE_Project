# main.py
import simpy
import config
from classes.buffet_system import BuffetSystem
from classes.analysis import Analysis
from core.theoretical_calculator import TheoreticalCalculator

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
def run_theoretical_calculation():
    calc = TheoreticalCalculator()
    res = calc.compute_all()

    print("\n--- KET QUA TINH TOAN LY THUYET ---")
    for st, r in res.items():
        print(f"\n>>> {st}")
        print(f"λ_est        : {r['lambda_est']:.2f}")
        print(f"ρ            : {r['rho']:.3f}")
        print(f"P(block)     : {r['P_block']*100:.2f}%")
        print(f"Wq (minutes) : {r['Wq']:.3f}")
if __name__ == "__main__":
    run_simulation()
    run_theoretical_calculation()