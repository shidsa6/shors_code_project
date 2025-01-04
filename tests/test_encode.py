import unittest
from qiskit import QuantumCircuit
from src.encode import create_shors_code

class TestShorsCodeEncoding(unittest.TestCase):
    def test_create_shors_code(self):
        """Test the Shor's 9-qubit encoding circuit."""
        # Generate the Shor code circuit
        qc = create_shors_code()
        
        # Verify the number of qubits
        self.assertEqual(qc.num_qubits, 9, "The circuit should have 9 qubits.")
        
        # Extract gate operations, excluding barriers
        instructions = [gate[0].name for gate in qc.data if gate[0].name != 'barrier']
        
        # Expected sequence of gates (without barriers)
        expected_gates = ['cx', 'cx', 'h', 'h', 'h', 'cx', 'cx', 'cx', 'cx', 'cx', 'cx']
        
        # Compare each gate to the expected sequence
        for i, (expected, actual) in enumerate(zip(expected_gates, instructions)):
            self.assertEqual(expected, actual, f"Step {i}: Expected gate {expected}, but got {actual}.")

if __name__ == "__main__":
    unittest.main()
