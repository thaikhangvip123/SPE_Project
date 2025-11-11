# core/queue_system_factory.py
import simpy
from classes.analysis import Analysis

# Import các mô hình cụ thể
from models.fcfs import FCFSModel
from models.sjf import SJFModel
from models.ros import ROSModel
# from models.dynamic_server import DynamicServerModel # (Sẽ thêm sau)

class QueueSystemFactory:
    """
    Sử dụng Factory Pattern  để tạo các đối tượng mô hình hàng đợi
    dựa trên cấu hình.
    """
    def create_queue_model(self, env: simpy.Environment, config: dict, 
                             analyzer: Analysis, station_name: str):
        
        discipline = config['discipline']
        num_servers = config['servers']
        avg_service_time = config['avg_service_time']
        
        common_args = (env, num_servers, avg_service_time, analyzer, station_name)
        
        if discipline == 'FCFS':
            return FCFSModel(*common_args)
        
        elif discipline == 'SJF':
            return SJFModel(*common_args)
        
        elif discipline == 'ROS':
            return ROSModel(*common_args)
        
        # Thêm các mô hình khác ở đây...
        
        else:
            raise ValueError(f"Kỷ luật hàng đợi không xác định: {discipline}")