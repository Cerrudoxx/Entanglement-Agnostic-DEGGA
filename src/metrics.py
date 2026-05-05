import time

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"[METRICS] Tiempo total: {elapsed:.4f} s", flush=True)
        
        return (result[0], elapsed) + result[2:]
        
    return wrapper

def get_circuit_metrics(qc_a, qc_b):
    """Extrae profundidad y número de puertas dinámicamente."""
    try:
        metrics = {
            f"Alice ({qc_a.num_qubits}Q)": {
                "Depth": getattr(qc_a, 'depth', lambda: "N/A")(),
                "Gates": len(qc_a.instructions)
            },
            f"Bob ({qc_b.num_qubits}Q)": {
                "Depth": getattr(qc_b, 'depth', lambda: "N/A")(),
                "Gates": len(qc_b.instructions)
            }
        }
        return metrics
    except Exception:
        return "Error al extraer métricas."