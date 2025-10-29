import simpy
from system.multiqueue_system import MultiQueueSystem
from config import CONFIG
from classes.customer import Customer  # Assuming customer.py exists
from classes.analysis import Analysis  # Assuming analysis.py exists

def main():
    env = simpy.Environment()
    CONFIG["analysis"] = Analysis()
    system = MultiQueueSystem(env, CONFIG)
    system.run(until=10000)  # Simulate for 10000 time units
    CONFIG["analysis"].print_report()

if __name__ == "__main__":
    main()