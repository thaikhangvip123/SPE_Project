import simpy
from config import (
    SEED, SIM_TIME, ARRIVAL_RATES, STATION_CONFIGS,
    POLICY, SYSTEM_TYPE,
    THEORY_MODEL, THEORY_LAMBDA, THEORY_MU, THEORY_C, THEORY_K,
    CUSTOMER_TYPE_DISTRIBUTION, CUSTOMER_BASE_SERVICE,
    PROBABILITY_MATRICES, ROUTING_MODE, CONTINUE_PROBABILITY
)
from system.queue_system_factory import QueueSystemFactory
from system.validation_analyzer import ValidationAnalyzer

# === Create environment ===
env = simpy.Environment()

# === Create system dynamically ===
system = QueueSystemFactory.make_system(
    system_type=SYSTEM_TYPE,
    env=env,
    station_configs=STATION_CONFIGS,
    arrival_rates=ARRIVAL_RATES,
    seed=SEED,
    policy=POLICY,
    customer_type_distribution=CUSTOMER_TYPE_DISTRIBUTION,
    customer_base_service=CUSTOMER_BASE_SERVICE,
    probability_matrices=PROBABILITY_MATRICES,
    routing_mode=ROUTING_MODE,
    continue_probability=CONTINUE_PROBABILITY
)

# === Run simulation ===
system.run(until=SIM_TIME)

# === Compare with theoretical results ===
val = ValidationAnalyzer(system.analyzer)

if THEORY_MODEL == 'MM1':
    result = val.compare_mm1(THEORY_LAMBDA, THEORY_MU)
elif THEORY_MODEL == 'MMc':
    from system.theoretical_calculator import TheoreticalCalculator
    theory = TheoreticalCalculator.mmc(THEORY_LAMBDA, THEORY_MU, THEORY_C)
    sim = system.analyzer.calculate_statistics()
    result = {'theory': theory, 'sim': sim}
elif THEORY_MODEL == 'MMcK':
    from system.theoretical_calculator import TheoreticalCalculator
    theory = TheoreticalCalculator.mmc_k(THEORY_LAMBDA, THEORY_MU, THEORY_C, THEORY_K)
    sim = system.analyzer.calculate_statistics()
    result = {'theory': theory, 'sim': sim}
else:
    result = None

# === Print comparison ===
if result:
    print('\n--- Validation ---')
    if 'theory' in result and 'sim' in result:
        theory = result['theory']
        sim = result['sim']
        print(f"Theoretical W: {theory.get('W', 'N/A')}")
        print(f"Simulated W: {sim.get('avg_wait', 'N/A')}")
        if 'diff' in result:
            print(f"Difference: {result['diff']}")
    else:
        print("Result format:", result)
