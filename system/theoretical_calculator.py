import math


class TheoreticalCalculator:
    """Analytical formulas for M/M/1 and M/M/c and M/M/c/K systems.


    Methods return dictionaries with keys like rho, L, Lq, W, Wq, P0.
    """
    @staticmethod
    def mm1(lmbda, mu):
        if lmbda >= mu:
            raise ValueError('For M/M/1, lambda must be < mu')
        rho = lmbda / mu
        L = rho / (1 - rho)
        Lq = rho ** 2 / (1 - rho)
        W = 1 / (mu - lmbda)
        Wq = rho / (mu - lmbda)
        P0 = 1 - rho
        return {'rho': rho, 'L': L, 'Lq': Lq, 'W': W, 'Wq': Wq, 'P0': P0}

    @staticmethod
    def mmc(lmbda, mu, c):
        # returns M/M/c with infinite capacity
        rho = lmbda / (c * mu)
        if rho >= 1:
            raise ValueError('System unstable: rho >= 1 for M/M/c')
        # compute P0
        sum_terms = sum((lmbda / mu) ** n / math.factorial(n) for n in range(c))
        last = (lmbda / mu) ** c / (math.factorial(c) * (1 - rho))
        P0 = 1.0 / (sum_terms + last)
        Lq = (P0 * (lmbda / mu) ** c * rho) / (math.factorial(c) * (1 - rho) ** 2)
        L = Lq + lmbda / mu
        Wq = Lq / lmbda
        W = Wq + 1 / mu
        return {'rho': rho, 'L': L, 'Lq': Lq, 'W': W, 'Wq': Wq, 'P0': P0}

    @staticmethod
    def mmc_k(lmbda, mu, c, K):
        # M/M/c/K finite capacity. Use standard Erlang B/C style calculations.
        # For simplicity, we compute probabilities via state probabilities.
        probs = []
        # normalization constant
        for n in range(0, c):
            probs.append((lmbda ** n) / (math.factorial(n) * (mu ** n)))
        for n in range(c, K + 1):
            probs.append((lmbda ** n) / (math.factorial(c) * (c ** (n - c)) * (mu ** n)))
        P0 = 1.0 / sum(probs)
        # compute blocking prob: P_K
        PK = probs[K] * P0
        # effective arrival rate
        lmbda_eff = lmbda * (1 - PK)
        # compute L via sum n*Pn
        Pn = [p * P0 for p in probs]
        L = sum(n * Pn[n] for n in range(len(Pn)))
        return {'P0': P0, 'PK': PK, 'lmbda_eff': lmbda_eff, 'L': L}