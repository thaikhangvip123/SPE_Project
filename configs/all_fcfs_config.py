ALL_FCFS_CONFIG = {
    "UNTIL_TIME": 1000.0,

    "ARRIVAL_RATES": {
        0: 12,
        1: 13
    },

    "DEFAULT_PATIENCE_TIME": 15.0,

    "CUSTOMER_TYPE_DISTRIBUTION": {
        'normal': 0.70,
        'indulgent': 0.10,
        'impatient': 0.15,
        'erratic': 0.05
    },

    "PATIENCE_TIME_FACTORS": {
        'normal': 1.0,
        'indulgent': 1.0,
        'impatient': 0.5,
        'erratic': 1.0
    },

    "ERRATIC_DELAY_AMOUNT": 0.2,

    "DEFAULT_SERVICE_TIMES": {
        'Meat': 0.7,
        'Seafood': 0.5,
        'Dessert': 0.8,
        'Fruit': 0.3
    },

    "STATIONS": {
        'Meat':    {'servers': 5, 'capacity_K': 10, 'discipline': 'FCFS', 'avg_service_time': 0.5},
        'Seafood': {'servers': 7, 'capacity_K': 10, 'discipline': 'FCFS', 'avg_service_time': 0.3},
        'Dessert': {'servers': 7, 'capacity_K': 10, 'discipline': 'FCFS', 'avg_service_time': 0.5},
        'Fruit':   {'servers':10, 'capacity_K': 10, 'discipline': 'FCFS', 'avg_service_time': 0.3},
    },

    "PROB_MATRICES": {
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