# config.py

import importlib
import os
import sys

def load_config(config_name: str):
    """Load config dict from configs/<config_name>.py"""
    module = importlib.import_module(f"configs.{config_name}")
    return module.ALL_FCFS_CONFIG  


# ============ CHỌN CONFIG =============
DEFAULT_CONFIG = "all_fcfs_config"
CONFIG_NAME = os.getenv("SPE_CONFIG", DEFAULT_CONFIG)

# Load dict
config_dict = load_config(CONFIG_NAME)

# ============ BIẾN DICTIONARY → BIẾN MODULE =============
# Gán từng key/value vào module config
this_module = sys.modules[__name__]

for key, value in config_dict.items():
    setattr(this_module, key, value)

# ================== DONE ==================
