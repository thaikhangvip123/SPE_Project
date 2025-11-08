"""Utility functions for customer generation."""
import random


def select_customer_type(rng, type_distribution):
    """Select a customer type based on probability distribution.
    
    Args:
        rng: Random number generator
        type_distribution: Dict mapping customer types to probabilities
                          (e.g., {'normal': 0.7, 'impatient': 0.2, ...})
    
    Returns:
        str: Selected customer type
    """
    rand = rng.random()
    cumulative = 0.0
    
    # Normalize probabilities if they don't sum to 1.0
    total = sum(type_distribution.values())
    if total == 0:
        return 'normal'  # Default fallback
    
    for customer_type, probability in type_distribution.items():
        cumulative += probability / total
        if rand <= cumulative:
            return customer_type
    
    # Fallback to last type if rounding issues occur
    return list(type_distribution.keys())[-1] if type_distribution else 'normal'

