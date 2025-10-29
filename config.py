CONFIG = {
    "arrival_rates": [5.0, 3.0],
    "total_servers": 12,
    "dynamic_shared": True,
    "stations": {
        "meat": {"c": 4, "service_time": 1.0, "K": 20, "discipline": "ROS"},
        "seafood": {"c": 3, "service_time": 1.2, "K": 15, "discipline": "SJF"},
        "dessert": {"c": 3, "service_time": 0.8, "K": 12, "discipline": "DYNAMIC"},
        "grab": {"c": 2, "service_time": 0.5, "K": None, "discipline": "ROS"},
    },
    "prob_matrices": [
        # Gate 0 (example, adjust based on report)
        [[0.4, 0.2, 0.1, 0.1, 0.2], [0.1, 0.5, 0.1, 0.1, 0.2], [0.0, 0.0, 0.6, 0.2, 0.2], [0.0, 0.0, 0.0, 0.7, 0.3]],
        # Gate 1
        [[0.1, 0.1, 0.4, 0.2, 0.2], [0.2, 0.3, 0.2, 0.1, 0.2], [0.3, 0.2, 0.1, 0.1, 0.3], [0.0, 0.0, 0.0, 0.7, 0.3]]
    ],
    "customer_types": {"normal": 0.7, "indulgent": 0.15, "impatient": 0.1, "erratic": 0.05},
    "analysis": None,
}