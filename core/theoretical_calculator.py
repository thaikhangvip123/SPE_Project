# core/theoretical_calculator.py
import math
import config
# core/theoretical_calculator.py

class TheoreticalCalculator:

    def __init__(self):
        self.stations = config.STATIONS
        self.arrival_rates = config.ARRIVAL_RATES

        # Tổng arrival vào hệ thống
        self.lambda_total = sum(self.arrival_rates.values())

        # Ước lượng phân phối đến từng quầy từ PROB_MATRICES['initial']
        self.initial_matrix = config.PROB_MATRICES['initial']

    # ============================================================
    def estimate_lambda_station(self, station_name):
        """Ước lượng arrival vào từng quầy từ initial probability."""

        lam = 0
        for gate, lam_gate in self.arrival_rates.items():
            prob = self.initial_matrix[gate].get(station_name, 0)
            lam += lam_gate * prob

        # Sau đó khách quay lại 70% → coi như tăng 1/(1-0.7)
        lam *= 1 / 0.3   # feedback factor

        return lam

    # ============================================================
    def mmc_k_distribution(self, lam, mu, c, K):
        """Trả về phân phối trạng thái P(n) của M/M/c/K."""
        P = [0] * (K + 1)
        rho = lam / (c * mu)

        # P0 dùng công thức normalization
        sum1 = sum((lam ** n) / (math.factorial(n) * (mu ** n)) for n in range(c))
        sum2 = ((lam ** c) / (math.factorial(c) * (mu ** c))) * sum(
            (lam / (c * mu)) ** k for k in range(K - c + 1)
        )
        P0 = 1 / (sum1 + sum2)
        P[0] = P0

        for n in range(1, K + 1):
            if n <= c:
                P[n] = (lam ** n / (math.factorial(n) * mu ** n)) * P0
            else:
                P[n] = (
                    (lam ** c / (math.factorial(c) * mu ** c))
                    * ((lam / (c * mu)) ** (n - c))
                    * P0
                )

        return P

    # ============================================================
    def compute_station(self, station_name):
        st = self.stations[station_name]

        lam = self.estimate_lambda_station(station_name)
        mu = 1 / st['avg_service_time']
        c = st['servers']
        K = st['capacity_K']

        P = self.mmc_k_distribution(lam, mu, c, K)

        # blocking probability
        P_block = P[K]

        # Lq
        Lq = sum((n - c) * P[n] for n in range(c, K + 1))

        # effective arrival (không bị chặn)
        lam_eff = lam * (1 - P_block)

        # Wq (approx)
        Wq = Lq / lam_eff if lam_eff > 0 else 0

        return {
            "lambda_est": lam,
            "mu": mu,
            "rho": lam / (c * mu),
            "P_block": P_block,
            "Lq": Lq,
            "Wq": Wq
        }

    # ============================================================
    def compute_all(self):
        result = {}
        for st in self.stations.keys():
            result[st] = self.compute_station(st)
        return result
class ValidationAnalyzer:
    """So sánh kết quả mô phỏng với lý thuyết[cite: 85]."""
    def __init__(self, sim_analyzer, theo_calculator):
        self.sim_analyzer = sim_analyzer
        self.theo_calculator = theo_calculator
        pass # Logic sẽ được thêm sau

# core/multi_queue_system.py
class MultiQueueSystem:
    """Mô phỏng hệ thống đa hàng đợi[cite: 86]."""
    def __init__(self):
        pass # Logic sẽ được thêm sau