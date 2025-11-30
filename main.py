# main.py
import simpy
import sys
import importlib.util
from pathlib import Path
from classes.buffet_system import BuffetSystem
from classes.analysis import Analysis

def load_config(config_name):
    """
    Load config file từ thư mục configs/.
    
    Args:
        config_name: Tên config file (không cần .py), ví dụ: 'all_ros', 'all_fcfs'
    
    Returns:
        Module config đã được load
    """
    configs_dir = Path(__file__).parent / "configs"
    config_file = configs_dir / f"{config_name}.py"
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file không tồn tại: {config_file}")
    
    # Load module từ file
    spec = importlib.util.spec_from_file_location(config_name, config_file)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    return config_module

def list_available_configs():
    """Liệt kê các config file có sẵn trong thư mục configs/"""
    configs_dir = Path(__file__).parent / "configs"
    config_files = sorted([f.stem for f in configs_dir.glob("*.py") if not f.name.startswith("__")])
    return config_files

def run_simulation(config_module):
    """
    Thiết lập và chạy mô phỏng chính.
    
    Args:
        config_module: Module config đã được load
    """
    
    # 1. Khởi tạo môi trường
    env = simpy.Environment()
    
    # 2. Khởi tạo bộ phân tích
    analyzer = Analysis()
    
    # 3. Khởi tạo hệ thống buffet (truyền config vào)
    buffet = BuffetSystem(env, analyzer, config_module)
    
    # 4. Chạy mô phỏng
    buffet.run(until_time=config_module.UNTIL_TIME)
    
    # 5. Tính toán và in kết quả
    analyzer.calculate_statistics()
    analyzer.print_report()

def main():
    """Hàm main với menu chọn config"""
    available_configs = list_available_configs()
    
    # Kiểm tra nếu có argument từ command line
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    else:
        # Hiển thị menu để chọn
        print("=== CHON CONFIG FILE ===")
        print("Các config có sẵn:")
        for i, config_name in enumerate(available_configs, 1):
            print(f"  {i}. {config_name}")
        print(f"  0. Thoát")
        
        try:
            choice = input("\nNhập số thứ tự config (hoặc tên config): ").strip()
            
            # Nếu là số, chọn theo index
            if choice.isdigit():
                idx = int(choice)
                if idx == 0:
                    print("Thoát chương trình.")
                    return
                if 1 <= idx <= len(available_configs):
                    config_name = available_configs[idx - 1]
                else:
                    print(f"Lỗi: Số không hợp lệ. Vui lòng chọn từ 1 đến {len(available_configs)}")
                    return
            else:
                # Nếu là tên config
                config_name = choice
        except KeyboardInterrupt:
            print("\nThoát chương trình.")
            return
        except Exception as e:
            print(f"Lỗi: {e}")
            return
    
    # Load và chạy config
    try:
        print(f"\n=== Dang chay config: {config_name} ===")
        config_module = load_config(config_name)
        run_simulation(config_module)
    except FileNotFoundError as e:
        print(f"Lỗi: {e}")
        print(f"Các config có sẵn: {', '.join(available_configs)}")
    except Exception as e:
        print(f"Lỗi khi chạy mô phỏng: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()