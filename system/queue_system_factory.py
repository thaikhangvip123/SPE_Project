
from typing import Type, Dict
from models.ros_model import ROSQueue
from models.sjf_model import SJFQueue
# from .dynamic import DynamicQueue

_FACTORY: Dict[str, Type[BaseQueueSystem]] = {
    "ROS": ROSQueue,
    "SJF": SJFQueue,
    "DYNAMIC": DynamicQueue,
}

def create_queue(discipline: str, env, servers, avg_service_rate,
                 capacity_K=None, **extra):
    cls = _FACTORY[discipline.upper()]
    return cls(env, servers, avg_service_rate, capacity_K, **extra)