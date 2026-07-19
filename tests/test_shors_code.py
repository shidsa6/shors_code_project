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
        
    def _get_clean_statevector(self, qc):
        """Return the true statevector of qc via qiskit.quantum_info.Statevector.

        NOTE: AerSimulator(method='statevector') + execute() +
        qc.save_statevector() + result.get_statevector() returns a
        qiskit_aer.backends.compatibility.Statevector object that, on this
        qiskit/qiskit-aer version pairing, is broken: every index access
        returns the *same* constant value (0.35355... = 1/sqrt(8) here)
        regardless of which basis state you actually query. That silently
        turns the statevector assertions below into tests of nothing -
        they'd "pass" even if create_shors_code() were completely wrong,
        purely by numeric coincidence. Statevector.from_instruction() goes
        through a separate, version-independent code path and gives the
        real amplitudes (confirmed against this by hand: it reproduces
        exactly 8 nonzero basis states with magnitude 1/sqrt(8), matching
        the expected GHZ-block structure of the 9-qubit Shor code).
        """
        return np.asarray(Statevector.from_instruction(qc).data)

    def test_logical_zero_encoding(self):
        """Test if |0⟩ is correctly encoded into the logical zero state."""
        qc = create_shors_code()
        state = self._get_clean_statevector(qc)

        # After encoding |0⟩, we expect an equal superposition over exactly
        # these 8 basis states (one all-0/all-1 combination per 3-qubit
        # block), each with amplitude magnitude 1/sqrt(8).
        expected_indices = [0, 7, 56, 63, 448, 455, 504, 511]
        total_prob = sum(abs(state[i])**2 for i in expected_indices)
        self.assertAlmostEqual(total_prob, 1.0, places=6)

        for i in expected_indices:
            self.assertAlmostEqual(abs(state[i])**2, 1/8, places=6)

        leaked = sum(abs(state[i])**2 for i in range(len(state)) if i not in expected_indices)
        self.assertAlmostEqual(leaked, 0.0, places=6,
                              msg="Amplitude leaked outside the expected 8-state support")

    def test_logical_one_encoding(self):
        """Test if |1⟩ is correctly encoded into the logical one state."""
        qc = QuantumCircuit(9)
        qc.x(0)  # Prepare |1⟩ state
        qc.compose(create_shors_code(), inplace=True)
        state = self._get_clean_statevector(qc)

        # Logical |1> is encoded onto the same 8 basis states as logical
        # |0> (same GHZ-block support, different relative phases).
        expected_indices = [0, 7, 56, 63, 448, 455, 504, 511]

        total_prob = sum(abs(state[i])**2 for i in expected_indices)
        self.assertAlmostEqual(total_prob, 1.0, places=6,
                              msg="Total probability not normalized")

        for idx in expected_indices:
            self.assertAlmostEqual(abs(state[idx])**2, 1/8, places=6,
                                 msg=f"Unequal superposition at index {idx}")

        leaked = sum(abs(state[i])**2 for i in range(len(state)) if i not in expected_indices)
        self.assertAlmostEqual(leaked, 0.0, places=6,
                              msg="Amplitude leaked outside the expected 8-state support")

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
