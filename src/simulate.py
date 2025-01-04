from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_aer.noise import depolarizing_error
from qiskit import execute
import sys
from os.path import dirname, abspath

# Add the project root directory to Python path
sys.path.append(dirname(dirname(abspath(__file__))))

from src.encode import create_shors_code
from src.decode import decode_shors_code

def create_noise_model():
    """Create a realistic noise model."""
    noise_model = NoiseModel()
    
    # Improved error probabilities for more realistic simulation
    p1 = 0.001  # Increase single-qubit error rate to 0.1%
    p2 = 0.01   # Increase two-qubit error rate to 1%
    
    # Add thermal relaxation error
    t1 = 50e3  # T1 relaxation time (50 microseconds)
    t2 = 70e3  # T2 relaxation time (70 microseconds)
    
    # Single-qubit depolarizing noise
    error_1 = depolarizing_error(p1, 1)
    noise_model.add_all_qubit_quantum_error(error_1, ['x', 'h', 'z'])
    
    # Two-qubit depolarizing noise
    error_2 = depolarizing_error(p2, 2)
    noise_model.add_all_qubit_quantum_error(error_2, ['cx'])
    
    return noise_model

def introduce_error(qc, qubit, error_type='bit'):
    """Introduce a single error on the specified qubit."""
    if error_type == 'bit':
        qc.x(qubit)  # Bit-flip error
    elif error_type == 'phase':
        qc.z(qubit)  # Phase-flip error
    elif error_type == 'both':
        qc.x(qubit)
        qc.z(qubit)

def simulate_shors_code(error_qubit=3, error_type='both', initial_state='0'):
    """Simulates Shor's 9-qubit code with a single error using AerSimulator."""
    # Create simulator with minimal noise
    noise_model = create_noise_model()
    backend = AerSimulator(noise_model=noise_model)
    qr = QuantumRegister(9, 'q')
    cr = ClassicalRegister(1, 'c')
    full_circuit = QuantumCircuit(qr, cr)

    # Initial state preparation
    if initial_state == '1':
        full_circuit.x(0)
    
    # Add encoding circuit
    full_circuit.compose(create_shors_code(), inplace=True)
    full_circuit.barrier()

    # Add error if specified
    if error_type != 'none':
        if error_type == 'bit':
            full_circuit.x(error_qubit)
        elif error_type == 'phase':
            full_circuit.z(error_qubit)
        elif error_type == 'both':
            full_circuit.x(error_qubit)
            full_circuit.z(error_qubit)
    full_circuit.barrier()
    
    # Decode and measure
    full_circuit.compose(decode_shors_code(), inplace=True)
    full_circuit.measure(0, 0)

    # Run simulation with noise model
    job = execute(
        full_circuit, 
        backend,
        shots=8192,
        noise_model=noise_model
    )
    result = job.result()
    counts = result.get_counts()
    
    # Calculate and print success rate
    total = sum(counts.values())
    expected_state = initial_state
    success = counts.get(expected_state, 0)
    success_rate = (success / total) * 100
    
    print(f"Initial state: |{initial_state}⟩")
    print(f"Error type: {error_type}")
    print(f"Counts: {counts}")
    print(f"Success rate: {success_rate:.1f}% (preservation of |{initial_state}⟩ state)")
    
    return full_circuit, counts
