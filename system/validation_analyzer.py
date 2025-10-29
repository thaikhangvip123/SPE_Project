from system.theoretical_calculator import mmck

class ValidationAnalyzer:
    def __init__(self, queue, lambda_, mu, c, K=None):
        self.q = queue
        self.lambda_ = lambda_
        self.mu = mu
        self.c = c
        self.K = K
        self.theory = mmck(lambda_, mu, c, K)

    def report(self, tolerance=0.05):
        sim_Wq = sum(self.q.wait_times)/len(self.q.wait_times) if self.q.wait_times else 0
        sim_Pb = self.q.blocked / (self.q.blocked + len(self.q.wait_times)) if (self.q.blocked + len(self.q.wait_times)) else 0
        # Lq approximation via Little's law or snapshots
        sim_Lq = self.lambda_ * sim_Wq

        diff = {
            "Wq": abs(sim_Wq - self.theory["Wq"]) / self.theory["Wq"] if self.theory["Wq"] else 0,
            "Lq": abs(sim_Lq - self.theory["Lq"]) / self.theory["Lq"] if self.theory["Lq"] else 0,
            "Pb": abs(sim_Pb - self.theory["Pb"]) if self.K else 0
        }

        ok = all(v < tolerance for v in diff.values())
        print("Validation", "PASSED" if ok else "FAILED")
        for k, v in diff.items():
            print(f"  {k}: sim={getattr(sim, k.lower(), 0):.4f} theory={self.theory[k]:.4f} Δ={v:.2%}")
        return ok