import simpy
from config import (
    SEED, SIM_TIME, ARRIVAL_RATES, STATION_CONFIGS,
    POLICY, SYSTEM_TYPE,
    THEORY_MODEL, THEORY_LAMBDA, THEORY_MU, THEORY_C, THEORY_K
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
    policy=POLICY
)

# === Run simulation ===
system.run(util_time=SIM_TIME)

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
    print('\\n--- Validation ---')
    print('Theoretical W:', result['theory'].get('W', 'N/A'))
    print('Simulated W:', result['sim']['avg_wait'])
