from system.base_queue_system import BaseQueueSystem

class ROSQueue(BaseQueueSystem):
    def _select_next(self) -> 'Customer':
        return random.choice(self.waiting)