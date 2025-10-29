from system.base_queue_system import BaseQueueSystem

class SJFQueue(BaseQueueSystem):
    STARVATION_THRESHOLD = 30.0

    def _select_next(self) -> 'Customer':
        def key(c: 'Customer'):
            starvation = (self.env.now - c.arrival_time) > self.STARVATION_THRESHOLD
            return (c.serve_time, 0 if starvation else (self.env.now - c.arrival_time))
        return min(self.waiting, key=key)