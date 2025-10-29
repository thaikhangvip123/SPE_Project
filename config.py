# ===================== FILE: config.py =====================

# === GLOBAL SETTINGS ===
SEED = 100           # random seed for reproducibility
SIM_TIME = 200      # total simulation time (time units)

# === ARRIVAL RATES (λ) ===
# Each gate or queue line’s arrival rate
ARRIVAL_RATES = (0.6, 0.4)  # total λ = 1.0

# === SERVICE STATION CONFIGURATION ===
# Each station: number of servers (c), capacity (K), avg service time (1/μ)
STATION_CONFIGS = {
    'fruit': {
        'c': 10,
        'K': 10,
        'avg': 0.7,
    },
    'meat': {
        'c': 10,
        'K': 10,
        'avg': 1.2,
    },
    'seafood': {
        'c': 7,
        'K': 10,
        'avg': 0.8,
    },
    'dessert': {
        'c': 7,
        'K': 10,
        'avg': 0.5,
    },
}

# === POLICY / QUEUE MODEL ===
# Choose from: 'ROS', 'SJF', 'DYNAMIC'
POLICY = 'SJF'

# === SYSTEM TYPE ===
# Choose 'single' for BuffetSystem or 'multi' for MultiQueueSystem
SYSTEM_TYPE = 'single'

# === VALIDATION MODEL ===
# Choose theoretical model type for comparison
# Supported: 'MM1', 'MMc', 'MMcK'
THEORY_MODEL = 'MMcK'

# === THEORETICAL PARAMETERS ===
# You can override theoretical λ, μ, c if needed
THEORY_LAMBDA = sum(ARRIVAL_RATES)
THEORY_MU = 1.0   # service rate (1 / avg service time)
THEORY_C = 10      # number of servers (for MMc)
THEORY_K = 10     # capacity (for MMcK)
