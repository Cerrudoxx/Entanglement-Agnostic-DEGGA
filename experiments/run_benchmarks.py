import sys
import os
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.grover_engine import DistributedGrover
from src.io_utils import save_results_to_csv

def get_topologies_for_q(q, strategy):
    if strategy == "all":
        return [f"{i}_to_{q-i}" for i in range(1, q)]
    elif strategy == "1_to_n":
        return [f"1_to_{q-1}"]
    elif strategy == "n_to_1":
        return [f"{q-1}_to_1"]
    elif strategy == "symmetric":
        n_a = q // 2
        n_b = q - n_a
        return [f"{n_a}_to_{n_b}"]
    else:
        try:
            n_a, n_b = map(int, strategy.split("_to_"))
            if n_a + n_b == q:
                return [strategy]
            return []
        except:
            raise ValueError(f"Estrategia de topología inválida: {strategy}")

def run_scalability_test(topology_strategy, execution_node):
    csv_path = "outputs/data/scalability_results.csv"
    
    test_cases = [
        {"q": 3,  "targets": ["001", "110"]},
        {"q": 4,  "targets": ["0011", "1100"]},
        {"q": 5,  "targets": ["00001", "00010", "00100"]},
        {"q": 6,  "targets": ["000000", "111111"]},
        {"q": 7,  "targets": ["1010101", "0101010"]},
        {"q": 8,  "targets": ["00001111", "11110000"]},
        {"q": 9,  "targets": ["100000001", "010000010", "001000100"]},
        {"q": 10, "targets": ["0000000000", "1111111111"]},
        {"q": 11, "targets": ["10101010101", "01010101010"]},
        {"q": 12, "targets": ["000000111111", "111111000000", "010101010101"]},
        {"q": 13, "targets": ["1111111000000", "0000000111111"]},
        {"q": 14, "targets": ["10000000000001", "01111111111110"]},
        {"q": 15, "targets": ["000000000000000", "111111111111111"]}
    ]
    
    for test in test_cases:
        q = test["q"]
        targets = test["targets"]
        topologies = get_topologies_for_q(q, topology_strategy)
        
        for topology in topologies:
            print(f"\n========================================================")
            print(f" LAUNCHING TEST: {q}Q | Topology: {topology} | Node: {execution_node}")
            print(f"========================================================")
            try:
                engine = DistributedGrover(q, targets, topology=topology)
                counts, exec_time, j_iters, phase, gates_a, gates_b = engine.generate_and_run(qpu_node=execution_node)
                
                top_states = sorted(counts, key=counts.get, reverse=True)[:len(targets)]
                
                print(f"\n[VALIDATION] Expected Targets : {targets}")
                results_str = "  ".join([f"|{state}> ({counts.get(state, 0)} shots)" for state in top_states])
                print(f"[VALIDATION] Obtained Results : {results_str}", flush=True)
                
                is_success = set(top_states) == set(targets)
                if is_success:
                    print("[VALIDATION] Status: SUCCESS")
                else:
                    print("[VALIDATION] Status: FAILED (Convergence discrepancy)")
                
                save_results_to_csv(
                    csv_path, q, targets, exec_time, counts, 
                    topology=topology, j_iters=j_iters, phase=phase, 
                    gates_a=gates_a, gates_b=gates_b, node=execution_node, success=is_success
                )
                
            except Exception as e:
                print(f"Failed on {q} qubits ({topology}): {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecución de benchmarks de escalabilidad CUNQA")
    parser.add_argument("-p", "--topology", default="all", help="Estrategias: 'all', '1_to_n', 'n_to_1', 'symmetric', o una específica (ej. '3_to_3')")
    parser.add_argument("-n", "--node", default="genofun", help="Nodo/Partición de Slurm para ejecución")
    
    args = parser.parse_args()
    run_scalability_test(args.topology, args.node)