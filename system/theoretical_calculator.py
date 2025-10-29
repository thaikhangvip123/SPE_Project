import math
from typing import Optional

def mmck(lambda_: float, mu: float, c: int, K: Optional[int] = None):
    rho = lambda_ / (c * mu)
    if rho >= 1:
        raise ValueError("System unstable (ρ ≥ 1)")

    sum_ = sum((lambda_ / mu)**n / math.factorial(n) for n in range(c))
    if K is None:
        p0 = 1 / (sum_ + (lambda_ / mu)**c / (math.factorial(c) * (1 - rho)))
        Lq = p0 * (lambda_ / mu)**c * rho / (math.factorial(c) * (1 - rho)**2)
    else:
        sum_k = sum_ + sum((lambda_ / mu)**n / (math.factorial(c) * c**(n-c)) for n in range(c, K+1))
        p0 = 1 / sum_k
        term = (lambda_ / mu)**c / math.factorial(c)
        Lq = p0 * term * rho / (1 - rho)**2 * (1 - (K-c+1)*rho**(K-c) + (K-c)*rho**(K-c+1))

    L = Lq + lambda_ / mu
    Wq = Lq / lambda_  # Simplified, adjust if blocking
    W = Wq + 1/mu

    Pb = 0.0 if K is None else p0 * (lambda_/mu)**K / (math.factorial(c)*c**(K-c))

    return {"rho": rho, "P0": p0, "Lq": Lq, "L": L, "Wq": Wq, "W": W, "Pb": Pb}