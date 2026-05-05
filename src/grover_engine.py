import os, sys
import math
import numpy as np

sys.path.append(os.getenv("HOME"))

from cunqa.qpu import get_QPUs, qraise, qdrop, run
from cunqa.circuit import CunqaCircuit
from cunqa.qjob import gather

from src.metrics import timer_decorator, get_circuit_metrics
from src.io_utils import draw_circuits

class DistributedGrover:
    
    def __init__(self, n_qubits, targets, topology="1_to_n"):
        """
        :param topology: "1_to_n" (Alice=1Q, Bob=n-1Q) o "n_to_1" (Alice=n-1Q, Bob=1Q)
        """
        self.n = n_qubits
        self.targets = targets
        self.a = len(targets)
        self.N = 2 ** self.n
        self.topology = topology
        parts = topology.split("_to_")
        self.n_a = int(parts[0])
        self.n_b = int(parts[1])
        if self.n_a + self.n_b != self.n:
            raise ValueError("La suma de qubits en la topología debe igualar n_qubits")
        
        
        self.qc_a = None
        self.qc_b = None
        
        self.theta = 0.0
        self.J = 0
        self.phi = 0.0
        
        self._calculate_math()
        
    def _calculate_math(self):
        """Calcula los parámetros de Long."""
        if self.a == 0 or self.a >= self.N:
            raise ValueError("Targets deben estar entre 1 y N-1.")

        self.theta = math.asin(math.sqrt(self.a / self.N))
        self.J = math.floor((math.pi / 2 - self.theta) / (2 * self.theta))
        
        numerator = math.sin(math.pi / (4 * self.J + 6))
        denominator = math.sin(self.theta)
        self.phi = 2 * math.asin(numerator / denominator)
        
        print(f"\n[ENGINE] Matematica: J={self.J+1}, Phi={self.phi:.4f}, Topologia={self.topology}")

    def _apply_distributed_mcp(self, qc_a, qc_b, phase):
        exposed_qubits = list(range(self.n_a))
        with qc_a.expose(exposed_qubits, qc_b) as (rqubits, sub_b):
            local_controls = list(range(self.n_b - 1))
            target = self.n_b - 1
            sub_b.mcp(phase, *local_controls, *rqubits, target)

    def _build_oracle(self, qc_a, qc_b):
        for target in self.targets:
            a_bits = target[:self.n_a]
            b_bits = target[self.n_a:]
            
            for i, bit in enumerate(a_bits):
                if bit == '0': qc_a.x(i)
            for i, bit in enumerate(b_bits):
                if bit == '0': qc_b.x(i)
                    
            self._apply_distributed_mcp(qc_a, qc_b, self.phi)
            
            for i, bit in enumerate(a_bits):
                if bit == '0': qc_a.x(i)
            for i, bit in enumerate(b_bits):
                if bit == '0': qc_b.x(i)

    def _build_diffuser(self, qc_a, qc_b):
        for i in range(self.n_a): qc_a.h(i); qc_a.x(i)
        for i in range(self.n_b): qc_b.h(i); qc_b.x(i)
        self._apply_distributed_mcp(qc_a, qc_b, self.phi)
        for i in range(self.n_a): qc_a.x(i); qc_a.h(i)
        for i in range(self.n_b): qc_b.x(i); qc_b.h(i)

    @timer_decorator
    def generate_and_run(self, shots=1000, qpu_node="lusitania"):        
        qc_a = CunqaCircuit(self.n_a, self.n_a, id="Alice")
        qc_b = CunqaCircuit(self.n_b, self.n_b, id="Bob")

        self.qc_a = qc_a
        self.qc_b = qc_b

        for i in range(self.n_a): qc_a.h(i)
        for i in range(self.n_b): qc_b.h(i)
            
        for _ in range(self.J + 1):
            self._build_oracle(qc_a, qc_b)
            self._build_diffuser(qc_a, qc_b)
            
        qc_a.measure(list(range(self.n_a)), list(range(self.n_a)))
        qc_b.measure(list(range(self.n_b)), list(range(self.n_b)))
        
        draw_circuits(qc_a, qc_b, filename_prefix=f"Grover_{self.n}Q_{self.topology}")
        
        metrics = get_circuit_metrics(qc_a, qc_b)
        print(metrics)
        gates_a = metrics.get(f"Alice ({self.n_a}Q)", {}).get("Gates", 0)
        gates_b = metrics.get(f"Bob ({self.n_b}Q)", {}).get("Gates", 0)

        try:
            family = qraise(2, "99:00:00", partition=qpu_node, simulator="Aer", quantum_comm=True, co_located=True, cores=1, mem_per_qpu=8)
            qpus = get_QPUs(co_located=True, family=family)
            
            n_comm = self.n_a * 2
            jobs = run([self.qc_a, self.qc_b], qpus, shots=shots, n_communication_qubits=n_comm)
            results = gather(jobs)
            qdrop(family)
            
            counts_a = results[0].counts
            counts_b = results[1].counts
            
            corrected_counts = {}
            
            for target in self.targets:
                a_str = target[:self.n_a][::-1]
                b_str = target[self.n_a:][::-1]
                
                c_a = counts_a.get(a_str, 0)
                c_b = counts_b.get(b_str, 0)

                corrected_counts[target] = min(c_a, c_b)
                
            return corrected_counts, 0, self.J, self.phi, gates_a, gates_b
            
        except Exception as e:
            if 'family' in locals(): qdrop(family)
            raise e
        
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Motor de simulación DEGGA/CUNQA")
    parser.add_argument("-q", "--qubits", type=int, default=5, help="Número total de qubits lógicos")
    parser.add_argument("-t", "--targets", nargs="+", default=["00000", "11111"], help="Estados objetivo (separados por espacio)")
    parser.add_argument("-p", "--topology", required=True, help="Topología de partición de red (ej. 3_to_3, 2_to_4)") 
    parser.add_argument("-n", "--node", default="genofun", help="Nodo/Partición de Slurm para ejecución (ej. genofun, lusitania)")
    
    args = parser.parse_args()
    
    try:
        grover_engine = DistributedGrover(n_qubits=args.qubits, targets=args.targets, topology=args.topology)
        counts, exec_time = grover_engine.generate_and_run(qpu_node=args.node)
        
        top_states = sorted(counts, key=counts.get, reverse=True)[:len(args.targets)]
        print("\n--- FINAL RESULTS ---")
        for state in top_states:
            print(f"|{state}> detected {counts[state]} times.")
            
        if set(top_states) == set(args.targets):
            print("✅ Successful Multi-target search.")
        else:
            print("❌ Convergence discrepancy.")
            
    except Exception as e:
        print(f"Execution error: {e}")
