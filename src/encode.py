from qiskit import QuantumCircuit

def create_shors_code():
    """Creates a 9-qubit Shor code circuit following the original sequence."""
    qc = QuantumCircuit(9)
    
    # First level: spread the state to three qubits
    qc.cx(0, 3)  # CNOT from q0 to q3
    qc.cx(0, 6)  # CNOT from q0 to q6
    
    # Convert to phase-flip code basis
    qc.h([0, 3, 6])
    
    # Second level: protect against bit flips within each block
    qc.cx(0, 1)
    qc.cx(0, 2)
    qc.cx(3, 4)
    qc.cx(3, 5)
    qc.cx(6, 7)
    qc.cx(6, 8)
    
    return qc
