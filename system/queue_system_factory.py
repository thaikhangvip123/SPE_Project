from classes.food_station import FoodStation


class QueueSystemFactory:
    """Factory that creates FoodStation objects and systems."""
    @staticmethod
    def make_station(name, env, **kwargs):
        return FoodStation(name, env, **kwargs)


    @staticmethod
    def make_system(system_type, env, station_configs, **kwargs):
        if system_type == 'single':
            from classes.buffet_system import BuffetSystem
            return BuffetSystem(env, station_configs, **kwargs)
        elif system_type == 'multi':
            from system.multiqueue_system import MultiQueueSystem
            return MultiQueueSystem(env, station_configs, **kwargs)
        else:
            raise ValueError(f"Unknown system_type={system_type}")