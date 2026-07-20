import os
import shutil
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Force matplotlib to not use X11
from datetime import datetime
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace, state_fidelity
from qiskit.visualization import plot_histogram

def setup_output_directory():
    """Setup the output directory for saving visualizations."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(current_dir, 'examples')
    
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def visualize_circuit(circuit):
    """Generate a clear circuit diagram."""
    output_dir = setup_output_directory()
    
    try:
        image_file = f"{output_dir}/shor_circuit.png"
        circuit.draw(
            output='mpl',
            filename=image_file,
            style={
                'backgroundcolor': '#FFFFFF',
                'textcolor': '#000000',
                'fontsize': 14,
                'subfontsize': 12,
                'showindex': True,
                'margin': [2.0, 0.2, 0.2, 0.3],
                'displaytext': {
                    "CNOT": "⊕",
                    "x": "E",    
                    "z": "E",    
                    "H": "H", 
                    "CCX": "T"
                },
                'displaycolor': {
                    'x': '#FF0000',   
                    'z': '#FF0000',   
                    'H': '#000000',
                    'CNOT': '#000000',
                    'CCX': '#000000'
                }
            },
            plot_barriers=True,
            initial_state=True
        )
        
        print(f"Circuit saved to: {image_file}")
        
    except Exception as e:
        print(f"Error saving circuit: {str(e)}")

def visualize_results(counts):
    """Generate results visualization."""
    output_dir = setup_output_directory()
    
    try:
        plt.figure(figsize=(12, 6))
        
        total_shots = sum(counts.values())
        success_rate = (counts.get('0', 0) / total_shots) * 100
        
        plot_histogram(
            counts,
            title=f"Shor's Code Results\nSuccess Rate: {success_rate:.1f}% (|0⟩ state)",
            bar_labels=True
        )
        
        filepath = os.path.join(output_dir, 'results.png')
        plt.savefig(filepath, bbox_inches='tight', dpi=300)
        plt.close()
        
        print(f"Results saved to: {filepath}")
        
    except Exception as e:
        print(f"Error saving results: {str(e)}")

def visualize_error_correction_performance(error_types=['bit', 'phase', 'both']):
    """Visualize the performance of error correction for different error types."""
    from src.simulate import simulate_shors_code
    
    plt.figure(figsize=(12, 6))
    
    results = {}
    success_rates = []
    
    for error_type in error_types:
        _, counts = simulate_shors_code(
            error_type=error_type,
            error_qubit=4,
            initial_state='0'  
        )
        results[f'{error_type}'] = counts
        
        total = sum(counts.values())
        success = counts.get('0', 0)  
        success_rate = (success / total) * 100
        
        print(f"{error_type}: {success}/{total} counts are |0⟩ = {success_rate:.1f}%")
        success_rates.append(f'{success_rate:.1f}%')

    title = "Shor Code Error Correction Results\n" + \
            "\n".join([f"{type}: {rate} successful |0⟩ preservation" 
                      for type, rate in zip(error_types, success_rates)])
    
    plot_histogram(
        results,
        title=title,
        legend=[f'{type} ({rate})' for type, rate in zip(error_types, success_rates)],
        bar_labels=True
    )
    plt.tight_layout()
    plt.show()


def _build_error_circuit(error_type, error_qubit, initial_state='0'):
    """Build encode -> inject single-qubit error -> decode, ideal (noiseless) circuit.

    Uses the actual encode/decode circuits from src.encode / src.decode, with no
    AerSimulator noise model involved, so the resulting statevector is exact.
    """
    from src.encode import create_shors_code
    from src.decode import decode_shors_code

    qc = QuantumCircuit(9)
    if initial_state == '1':
        qc.x(0)
    qc.compose(create_shors_code(), inplace=True)

    if error_type == 'bit':
        qc.x(error_qubit)
    elif error_type == 'phase':
        qc.z(error_qubit)
    elif error_type == 'both':
        qc.x(error_qubit)
        qc.z(error_qubit)

    qc.compose(decode_shors_code(), inplace=True)
    return qc


def compute_per_qubit_error_grid(initial_state='0'):
    """Compute recovery fidelity for a single-qubit error on each of the 9
    physical qubits, for each of 3 error types (bit-flip, phase-flip, both),
    using the ideal noiseless case.

    For each (qubit, error type) pair, this:
      1. Encodes logical |{initial_state}> with create_shors_code().
      2. Injects the error (X, Z, or X+Z) on that physical qubit right after
         encoding.
      3. Runs decode_shors_code().
      4. Gets the exact 9-qubit statevector via Statevector.from_instruction
         (NOT AerSimulator's save_statevector - see tests/test_shors_code.py
         for why that path is unreliable on this qiskit-aer version).
      5. Reduces that statevector to the logical qubit (qubit 0) alone via
         qiskit.quantum_info.partial_trace, tracing out the 8 syndrome/ancilla
         qubits. The decode circuit here is a coherent, measurement-free
         correction (Toffoli-based), so the ancilla qubits do not generally
         return to |0> even when the logical qubit is perfectly recovered -
         only the reduced state of qubit 0 is the meaningful "recovered
         logical qubit" to compare against.
      6. Computes fidelity of that reduced state against the expected pure
         logical state |{initial_state}> via qiskit.quantum_info.state_fidelity.

    Returns a (9, 3) numpy array of fidelities, rows = physical qubit index
    0-8, columns = ['bit', 'phase', 'both'].
    """
    error_types = ['bit', 'phase', 'both']
    expected_logical = DensityMatrix.from_label(initial_state)

    grid = np.zeros((9, len(error_types)))
    for qubit_idx in range(9):
        for col, error_type in enumerate(error_types):
            qc = _build_error_circuit(error_type, qubit_idx, initial_state=initial_state)
            full_state = Statevector.from_instruction(qc)
            reduced = partial_trace(full_state, [q for q in range(9) if q != 0])
            grid[qubit_idx, col] = state_fidelity(expected_logical, reduced)

    return grid, error_types


def generate_per_qubit_error_grid(initial_state='0'):
    """Generate and save the per-qubit, per-error-type recovery fidelity heatmap.

    Ideal (noiseless) case only: for each of the 9 physical qubits and each of
    3 single-qubit error types, encodes logical |{initial_state}>, injects the
    error on that one physical qubit, decodes, and measures how faithfully the
    logical qubit (qubit 0) is recovered. Saved to
    examples/per_qubit_error_correction.png at 200 dpi.
    """
    output_dir = setup_output_directory()
    grid, error_types = compute_per_qubit_error_grid(initial_state=initial_state)

    fidelity_min = grid.min()
    fidelity_max = grid.max()
    fidelity_mean = grid.mean()

    print("Per-qubit, per-error-type recovery fidelity (ideal, noiseless, "
          f"logical |{initial_state}>):")
    label_map = {'bit': 'bit-flip (X)', 'phase': 'phase-flip (Z)', 'both': 'combined (X+Z)'}
    for qubit_idx in range(9):
        row = "  ".join(
            f"{label_map[et]}={grid[qubit_idx, col]*100:.2f}%"
            for col, et in enumerate(error_types)
        )
        print(f"  qubit {qubit_idx}: {row}")
    print(f"Average fidelity: {fidelity_mean*100:.4f}%  "
          f"Min: {fidelity_min*100:.4f}%  Max: {fidelity_max*100:.4f}%")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    im = ax.imshow(grid.T, cmap='viridis', vmin=0.0, vmax=1.0, aspect='auto')

    ax.set_xticks(range(9))
    ax.set_xticklabels([str(i) for i in range(9)])
    ax.set_xlabel('Physical qubit index (0-8)')

    ax.set_yticks(range(len(error_types)))
    ax.set_yticklabels([label_map[et] for et in error_types])
    ax.set_ylabel('Injected error type')

    for col in range(len(error_types)):
        for qubit_idx in range(9):
            ax.text(qubit_idx, col, f"{grid[qubit_idx, col]*100:.1f}",
                     ha='center', va='center',
                     color='white' if grid[qubit_idx, col] < 0.5 else 'black',
                     fontsize=8)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Recovery fidelity of logical qubit')

    ax.set_title(
        "Shor's Code: Per-Qubit Recovery Fidelity (Ideal, No Noise)\n"
        f"Logical |{initial_state}> recovered on qubit 0 after single-qubit error "
        f"on any of the 9 physical qubits\n"
        f"Average: {fidelity_mean*100:.2f}%  Min: {fidelity_min*100:.2f}%  "
        f"Max: {fidelity_max*100:.2f}%"
    )
    plt.tight_layout()

    filepath = os.path.join(output_dir, 'per_qubit_error_correction.png')
    plt.savefig(filepath, bbox_inches='tight', dpi=200)
    plt.close()

    print(f"Per-qubit error correction grid saved to: {filepath}")
    return grid, error_types


if __name__ == "__main__":
    import sys
    from os.path import dirname, abspath
    sys.path.append(dirname(dirname(abspath(__file__))))
    generate_per_qubit_error_grid()
