import unittest
from src.simulate import simulate_shors_code

class TestSimulateShorsCode(unittest.TestCase):
    def setUp(self):
        """Initialize test parameters."""
        self.shots = 8192
        self.error_threshold = 0.85  # Adjusted to 85% for realistic noise

    def test_no_error(self):
        """Test simulation with no errors introduced."""
        _, counts = simulate_shors_code(error_qubit=3, error_type='none', initial_state='0')
        success_rate = counts.get('0', 0) / self.shots
        self.assertGreater(success_rate, self.error_threshold,
                          f"Expected success rate > {self.error_threshold*100}%, got {success_rate*100}%")

    def test_bit_flip_error(self):
        """Test simulation with a single bit-flip error."""
        _, counts = simulate_shors_code(error_qubit=3, error_type='bit', initial_state='0')
        self.assertGreater(counts.get('0', 0), 7500, "Results should be logical |0> after correcting a bit-flip error.")

    def test_phase_flip_error(self):
        """Test simulation with a single phase-flip error."""
        _, counts = simulate_shors_code(error_qubit=3, error_type='phase', initial_state='0')
        self.assertGreater(counts.get('0', 0), 6500, "Results should be logical |0> after correcting a phase-flip error.")

    def test_combined_error(self):
        """Test simulation with both bit-flip and phase-flip errors."""
        _, counts = simulate_shors_code(error_qubit=3, error_type='both', initial_state='0')
        self.assertGreater(counts.get('0', 0), 6000, "Results should be logical |0> after correcting both errors.")

if __name__ == "__main__":
    unittest.main()
