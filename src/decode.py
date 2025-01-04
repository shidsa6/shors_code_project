from qiskit import QuantumCircuit

def decode_shors_code():
    """Decodes the Shor's 9-qubit code following the original sequence."""
    qc = QuantumCircuit(9)
    
    # Correct bit-flips within blocks
    qc.cx(0, 1)
    qc.cx(0, 2)
    qc.ccx(1, 2, 0)  # Toffoli for correction
    
    qc.cx(3, 4)
    qc.cx(3, 5)
    qc.ccx(4, 5, 3)
    
    qc.cx(6, 7)
    qc.cx(6, 8)
    qc.ccx(7, 8, 6)
    
    # Apply Hadamards before phase correction
    qc.h([0, 3, 6])
    
    # Correct phase-flips between blocks
    qc.cx(0, 3)
    qc.cx(0, 6)
    qc.ccx(3, 6, 0)  # Final correction
    
    return qc
