# ===================== FILE: config.py =====================

# === GLOBAL SETTINGS ===
SEED = 100           # random seed for reproducibility
SIM_TIME = 2000      # total simulation time (time units)

# === ARRIVAL RATES (λ) ===
# Each gate or queue line's arrival rate
ARRIVAL_RATES = (0.6, 0.4)  # total λ = 1.0

# === CUSTOMER CONFIGURATION ===
# Customer type distribution: probability of each type
# Types: 'normal', 'impatient', 'indulgent', 'erratic'
CUSTOMER_TYPE_DISTRIBUTION = {
    'normal': 0.7,      # 70% normal customers
    'impatient': 0.2,   # 20% impatient customers
    'indulgent': 0.1,   # 10% indulgent customers
    'erratic': 0.0      # 0% erratic customers
}
# Base service time for customers (can be overridden per customer)
CUSTOMER_BASE_SERVICE = 1.0

# === PROBABILITY MATRICES FOR STATION SELECTION ===
# Probability matrices for each arrival gate (gate 0 and gate 1)
# Each matrix maps station names to probabilities (must sum to 1.0)
# Format: {gate_id: {station_name: probability}}
PROBABILITY_MATRICES = {
    0: {  # Gate 0 probabilities
        'fruit': 0.3,
        'meat': 0.4,
        'seafood': 0.2,
        'dessert': 0.1
    },
    1: {  # Gate 1 probabilities
        'fruit': 0.2,
        'meat': 0.3,
        'seafood': 0.3,
        'dessert': 0.2
    }
}

# === ROUTING MODE ===
# Choose routing strategy: 'random', 'shortest_wait', 'one_liner'
# 'random': random_choose() - choose station randomly
# 'shortest_wait': shortest_expected_wait() - choose station with fewest customers
# 'one_liner': one_liner() - visit all stations in sequence
ROUTING_MODE = 'one_liner'

# === CONTINUE PROBABILITY ===
# Probability that customer continues to another station after being served
# (0.4 means 40% chance to continue, 60% chance to exit)
CONTINUE_PROBABILITY = 0.4

# === STARVATION THRESHOLD (for SJF) ===
# Maximum wait time before forcing service (to prevent starvation)
STARVATION_THRESHOLD = 5.0

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
POLICY = 'ROS'

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
