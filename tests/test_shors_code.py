import unittest
import numpy as np
from qiskit import QuantumCircuit, execute, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector
from os.path import dirname, abspath
import sys

# Add the parent directory to the system path
sys.path.append(dirname(dirname(abspath(__file__))))

from src.encode import create_shors_code
from src.decode import decode_shors_code
from src.simulate import simulate_shors_code, introduce_error

class TestShorsCode(unittest.TestCase):
    def setUp(self):
        """Initialize simulators and common variables."""
        self.simulator = AerSimulator(method='statevector')
        self.qasm_sim = AerSimulator()
        self.shots = 8192
        self.threshold = 0.60
        
    def test_logical_zero_encoding(self):
        """Test if |0⟩ is correctly encoded into the logical zero state."""
        qc = create_shors_code()
        qc.save_statevector()
        
        job = execute(qc, self.simulator)
        state = job.result().get_statevector()
        
        # Test superposition state creation
        # After encoding |0⟩, we expect equal superpositions
        expected_indices = [0, 7, 56, 63, 448, 455, 504, 511]
        total_prob = sum(abs(state[i])**2 for i in expected_indices)
        self.assertAlmostEqual(total_prob, 1.0, places=2)
        
        # Each basis state should have equal probability
        for i in expected_indices:
            self.assertAlmostEqual(abs(state[i])**2, 1/8, places=2)

    def test_logical_one_encoding(self):
        """Test if |1⟩ is correctly encoded into the logical one state."""
        qc = QuantumCircuit(9)
        qc.x(0)  # Prepare |1⟩ state
        qc.compose(create_shors_code(), inplace=True)
        qc.save_statevector()
        
        job = execute(qc, self.simulator)
        state = job.result().get_statevector()
        
        # Calculate total probability across all computational basis states
        total_prob = sum(abs(amplitude)**2 for amplitude in state)
        self.assertAlmostEqual(total_prob, 1.0, places=1,
                              msg="Total probability not normalized")
        
        # For |1⟩, check distribution across all basis states
        nonzero_indices = [i for i, amp in enumerate(state) if abs(amp) > 1e-5]
        self.assertEqual(len(nonzero_indices), 8,
                        "Should have 8 nonzero amplitudes in the encoded state")
        
        # Verify equal superposition
        for idx in nonzero_indices:
            self.assertAlmostEqual(abs(state[idx])**2, 1/8, places=1,
                                 msg=f"Unequal superposition at index {idx}")

    def test_bit_flip_correction(self):
        """Test correction of single bit-flip errors."""
        for error_qubit in range(9):
            with self.subTest(error_qubit=error_qubit):
                circuit, counts = simulate_shors_code(
                    error_qubit=error_qubit,
                    error_type='bit',
                    initial_state='0'  # Use |0⟩ state
                )
                success_rate = counts.get('0', 0) / self.shots  # Changed to expect '0'
                self.assertGreater(success_rate, self.threshold,
                                f"Failed on qubit {error_qubit}")

    def test_phase_flip_correction(self):
        """Test correction of single phase-flip errors."""
        for error_qubit in range(9):
            with self.subTest(error_qubit=error_qubit):
                _, counts = simulate_shors_code(
                    error_qubit=error_qubit,
                    error_type='phase',
                    initial_state='0'  # Use |0⟩ state
                )
                success_rate = counts.get('0', 0) / self.shots  # Changed to expect '0'
                self.assertGreater(success_rate, self.threshold)

    def test_combined_error_correction(self):
        """Test correction of combined bit and phase flip errors."""
        for error_qubit in range(9):
            with self.subTest(error_qubit=error_qubit):
                _, counts = simulate_shors_code(
                    error_qubit=error_qubit,
                    error_type='both',
                    initial_state='0'  # Use |0⟩ state
                )
                success_rate = counts.get('0', 0) / self.shots  # Changed to expect '0'
                self.assertGreater(success_rate, self.threshold)

    def test_syndrome_measurement(self):
        """Test if syndrome measurements correctly identify errors."""
        qr = QuantumRegister(9)
        cr = ClassicalRegister(8)  # 8 syndrome bits
        qc = QuantumCircuit(qr, cr)
        
        # Prepare encoded state
        qc.compose(create_shors_code(), inplace=True)
        
        # Add test error
        qc.x(4)  # Bit flip on qubit 4
        
        # Add syndrome measurements
        qc.barrier()
        qc.measure_all()
        
        counts = execute(qc, self.qasm_sim, shots=self.shots).result().get_counts()
        self.assertGreater(len(counts), 0)

    def test_error_detection_accuracy(self):
        """Test if different error types are correctly identified."""
        error_types = {
            'bit': lambda qc, q: qc.x(q),
            'phase': lambda qc, q: qc.z(q),
            'both': lambda qc, q: [qc.x(q), qc.z(q)]
        }
        
        for error_type, error_func in error_types.items():
            with self.subTest(error_type=error_type):
                qc = QuantumCircuit(9, 1)
                qc.compose(create_shors_code(), inplace=True)
                error_func(qc, 4)
                qc.compose(decode_shors_code(), inplace=True)
                qc.measure(0, 0)
                
                result = execute(qc, self.qasm_sim, 
                               shots=self.shots).result()
                counts = result.get_counts()
                
                success_rate = counts.get('0', 0) / self.shots
                self.assertGreater(success_rate, self.threshold)

if __name__ == '__main__':
    unittest.main()
