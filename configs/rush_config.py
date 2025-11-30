# ===== RUSH HOURS SCENARIO CONFIG =====

RUSH_CONFIG = {
    "UNTIL_TIME": 1000.0,

    "ARRIVAL_RATES": {
        0: 26,  # more than double
        1: 24   # less than double
    },

    "DEFAULT_PATIENCE_TIME": 20.0,  # increased

    "CUSTOMER_TYPE_DISTRIBUTION": {
        'normal': 0.70,     # keep the same
        'indulgent': 0.05,  # less
        'impatient': 0.1,   # less
        'erratic': 0.15     # more
    },

    "PATIENCE_TIME_FACTORS": { # I have no idea what this does
        'normal': 1.0,
        'indulgent': 1.0,
        'impatient': 0.5,
        'erratic': 1.0
    },

    "ERRATIC_DELAY_AMOUNT": 0.15, # less

    "DEFAULT_SERVICE_TIMES": { # important to keep the same
        'Meat': 0.7,
        'Seafood': 0.5,
        'Dessert': 0.8,
        'Fruit': 0.3
    },

    "STATIONS": {
        'Meat':    {'servers': 5, 'capacity_K': 10, 'discipline': 'SJF', 'avg_service_time': 0.5},
        'Seafood': {'servers': 7, 'capacity_K': 10, 'discipline': 'SJF', 'avg_service_time': 0.3},
        'Dessert': {'servers': 7, 'capacity_K': 10, 'discipline': 'SJF', 'avg_service_time': 0.5},
        'Fruit':   {'servers':10, 'capacity_K': 10, 'discipline': 'SJF', 'avg_service_time': 0.3},
    },

    "PROB_MATRICES": { # keep the same
        'initial': {
            0: {'Meat': 0.4, 'Seafood': 0.3, 'Dessert': 0.2, 'Fruit': 0.2},
            1: {'Meat': 0.3, 'Seafood': 0.4, 'Dessert': 0.15,'Fruit': 0.15}
        },
        'next_action': {
            'More': 0.7,
            'Exit': 0.3
        },
        'transition': {
            'Meat': 0.25,
            'Seafood': 0.25,
            'Dessert': 0.25,
            'Fruit': 0.25
        }
    }
}
