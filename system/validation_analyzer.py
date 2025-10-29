from system.theoretical_calculator import TheoreticalCalculator


class ValidationAnalyzer:
    """Compare simulation statistics with theoretical values."""
    def __init__(self, analyzer):
        self.analyzer = analyzer


    def compare_mm1(self, lmbda, mu):
        theory = TheoreticalCalculator.mm1(lmbda, mu)
        sim = self.analyzer.calculate_statistics()
        return {
            'theory': theory,
            'sim': sim,
            'diff': {
                'avg_wait': abs(theory['W'] - sim['avg_wait']),
                'avg_service': abs((1.0 / mu) - sim['avg_service'])
            }
        }