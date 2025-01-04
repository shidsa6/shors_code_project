import unittest
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit import execute
import numpy as np
import sys
from os.path import dirname, abspath

sys.path.append(dirname(dirname(abspath(__file__))))
from src.decode import decode_shors_code
from src.encode import create_shors_code

class TestDecode(unittest.TestCase):
    def setUp(self):
        self.simulator = AerSimulator()
        self.statevector_sim = AerSimulator(method="statevector")
        
    def test_circuit_structure(self):
        """Test the basic structure of the decoding circuit."""
        qc = decode_shors_code()
        self.assertIsInstance(qc, QuantumCircuit)
        self.assertEqual(qc.num_qubits, 9)
        
        # Count expected gate types
        gate_counts = {}
        for gate in qc.data:
            name = gate[0].name
            gate_counts[name] = gate_counts.get(name, 0) + 1
            
        self.assertGreaterEqual(gate_counts.get('cx', 0), 6, "Should have at least 6 CNOT gates")
        self.assertGreaterEqual(gate_counts.get('ccx', 0), 1, "Should have at least 1 Toffoli gate")
        self.assertGreaterEqual(gate_counts.get('h', 0), 3, "Should have 3 Hadamard gates")

    def test_bit_flip_correction(self):
        """Test if the decoder can correct a bit flip error."""
        # Create full circuit with encoding and decoding
        qr = QuantumRegister(9)
        cr = ClassicalRegister(1)
        qc = QuantumCircuit(qr, cr)
        
        # Encode |1⟩ state
        qc.x(0)
        qc.compose(create_shors_code(), inplace=True)
        
        # Add bit-flip error on first qubit
        qc.x(0)
        
        # Decode
        qc.compose(decode_shors_code(), inplace=True)
        qc.measure(0, 0)
        
        # Execute
        result = execute(qc, self.simulator, shots=1024).result()
        counts = result.get_counts()
        
        # Should recover |1⟩ state
        self.assertGreater(counts.get('1', 0), 900, "Failed to correct bit-flip error")

    def test_phase_flip_correction(self):
        """Test if the decoder can correct a phase flip error."""
        qr = QuantumRegister(9)
        cr = ClassicalRegister(1)
        qc = QuantumCircuit(qr, cr)
        
        # Encode |1⟩ state
        qc.x(0)
        qc.compose(create_shors_code(), inplace=True)
        
        # Add phase-flip error
        qc.z(0)
        
        # Decode
        qc.compose(decode_shors_code(), inplace=True)
        qc.measure(0, 0)
        
        # Execute
        result = execute(qc, self.simulator, shots=1024).result()
        counts = result.get_counts()
        
        # Should recover |1⟩ state
        self.assertGreater(counts.get('1', 0), 900, "Failed to correct phase-flip error")

    def test_statevector_dimension(self):
        """Test the dimension of the statevector."""
        qc = decode_shors_code()
        # Add save_state instruction
        qc.save_statevector()
        
        # Use new simulator method
        job = execute(qc, self.statevector_sim)
        result = job.result()
        statevector = result.get_statevector()
        # Convert to numpy array for length check
        statevector_array = np.asarray(statevector)
        self.assertEqual(len(statevector_array), 2**9, 
                        "The statevector should have 512 components.")

if __name__ == '__main__':
    unittest.main()
