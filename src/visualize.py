import os
import shutil
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Force matplotlib to not use X11
from datetime import datetime
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
