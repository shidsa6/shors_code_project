import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend
import matplotlib.pyplot as plt
from os.path import dirname, abspath
import sys

# Add the parent directory to the system path
sys.path.append(dirname(dirname(abspath(__file__))))

from src.simulate import simulate_shors_code
from src.visualize import visualize_circuit, visualize_results

def main():
    # Run simulation with bit flip error
    circuit, counts = simulate_shors_code(error_qubit=4, error_type='bit')
    
    # Generate and save visualizations
    visualize_circuit(circuit)
    visualize_results(counts)
    
    # Print results
    print("\nSimulation Results:")
    for state, count in counts.items():
        print(f"State {state}: {count} counts")

if __name__ == "__main__":
    main()
