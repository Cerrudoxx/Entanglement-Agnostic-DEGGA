import csv
import os

def save_results_to_csv(filename, n_qubits, targets, execution_time, counts, topology="N/A", j_iters=0, phase=0.0, gates_a=0, gates_b=0, node="unknown", success=False):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    file_exists = os.path.isfile(filename)
    
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Qubits", "Topology", "Targets", "J", "Phase", "Gates_A", "Gates_B", "Node", "Success", "Time_s", "State", "Shots"])
            
        for state, shots in counts.items():
            writer.writerow([n_qubits, topology, "|".join(targets), j_iters, round(phase, 4), gates_a, gates_b, node, success, execution_time, state, shots])
            
    print(f"[IO] Resultados guardados en {filename}", flush=True)

def draw_circuits(qc_a, qc_b, filename_prefix="circuit"):
    os.makedirs("outputs/figures", exist_ok=True)
    try:
        with open(f"outputs/figures/{filename_prefix}_Alice.txt", "w") as f:
            f.write(str(qc_a))
        with open(f"outputs/figures/{filename_prefix}_Bob.txt", "w") as f:
            f.write(str(qc_b))
        print(f"[IO] Circuitos exportados: {filename_prefix}")
    except:
        print("[IO] No se pudo exportar el diagrama del circuito.")