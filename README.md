# Entanglement-Agnostic DEGGA via CUNQA

This repository contains the source code, experimental suite, and telemetry data for the paper: **"Implementing an Entanglement-Agnostic DEGGA via Virtual Quantum Communication using CUNQA"**.

This project provides a physical distribution architecture for the Distributed Exact Generalized Grover Algorithm (DEGGA). By leveraging the CUNQA distributed quantum computing emulator and the *Telegate* protocol, this suite demonstrates how to seamlessly preserve global entanglement in multi-target exact quantum searches without requiring manual, case-specific algorithmic refactoring of the oracle.

## 📁 Project Structure

The repository is organized into the following directory structure:

```text
.
├── experiments
│   ├── outputs
│   │   └── data
│   │       └── scalability_results.csv   # Empirical execution metrics and telemetry
│   └── run_benchmarks.py                 # Automated batch-processing suite for HPC
├── README.md
└── src
    ├── grover_engine.py                  # Core mathematical engine and dynamic circuit synthesis
    ├── io_utils.py                       # I/O operations (CSV writing, circuit diagram export)
    └── metrics.py                        # Telemetry decorators and resource counting
```

### Modules Overview

* **`src/grover_engine.py`**: The core middleware. It autonomously computes Long's exact mathematical parameters (iterations $J$, exact phase $\phi$) and dynamically constructs the local CUNQA circuits (`Alice` and `Bob`). It manages the network abstraction, automatically exposing qubits across the virtual channel.
* **`experiments/run_benchmarks.py`**: The orchestration module designed to autonomously deploy queries across the High-Performance Computing (HPC) cluster. It traverses the topological space (e.g., symmetric $m \to m$, asymmetric $1 \to n$).
* **`experiments/outputs/data/scalability_results.csv`**: Contains the execution logs including circuit depth, gate counts, execution time, and empirical state distribution (1,000 shots per topology).

## 🚀 Installation & Prerequisites

To run this simulation suite, you need Python 3.10+ and the CUNQA framework properly installed and configured.

> **Note:** The version of CUNQA utilized in this project was precisely developed and optimized for execution on the **Lusitania supercomputer**.

### HPC Environment (Lusitania)

To reproduce the execution environment on Lusitania, you can load the specific pre-configured module:

```bash
module load python/cunqa
```

Alternatively, you may load the standard dependency stack:

```bash
module load gcc/gcc-11.2.0 \
            cmake/cmake-3.26.6 \
            openblas/openblas-0.3.24 \
            openmpi/openmpi-4.1.2-gcc11.2.0 \
            python/python-3.10 \
            boost/boost-1.85.0
```

### Dependency Setup (Manual Compilation)

If you prefer to clone and compile the framework, use the adapted source code. For full reproducibility, all experiments presented in the paper were conducted using the fork at commit [`5c4e9a3`](https://github.com/Cerrudoxx/cunqa/tree/5c4e9a37f652c8c49642361f7ead06058db74a45).

1. **Install the required CUNQA branch:**
   ```bash
   git clone -b cunqa-ex-module-2 [https://github.com/Cerrudoxx/cunqa.git](https://github.com/Cerrudoxx/cunqa.git)
   cd cunqa
   git checkout 5c4e9a37f652c8c49642361f7ead06058db74a45
   # Follow CUNQA's documentation to compile the C++ backend and ZeroMQ layer
   ```

2. **Clone this experimental suite:**
   ```bash
   git clone [https://github.com/Cerrudoxx/Entanglement-Agnostic-DEGGA.git](https://github.com/Cerrudoxx/Entanglement-Agnostic-DEGGA.git)
   cd dqc_grover
   ```

3. **Install Python Dependencies:**
   ```bash
   pip install numpy
   ```

## 💻 Usage

### 1. Running the Automated Scalability Suite
To reproduce the experiments from the paper, use the `run_benchmarks.py` script. You can specify the topological strategy and the Slurm execution node.

```bash
python experiments/run_benchmarks.py --topology all --node lusitania
```

**Arguments:**
* `-p` or `--topology`: Strategy to test. Options include `all`, `1_to_n`, `n_to_1`, `symmetric`, or a specific custom partition (e.g., `3_to_2`). Default is `all`.
* `-n` or `--node`: Slurm partition or node name for execution (e.g., `lusitania`).

### 2. Standalone Execution (Grover Engine)
You can also run a specific search query directly using the engine script.

```bash
python src/grover_engine.py --qubits 5 --targets 00001 00010 --topology 2_to_3 --node lusitania
```

## 📊 Telemetry and Results
All successful (and timed-out) executions are logged in `experiments/outputs/data/scalability_results.csv`. The telemetry captures:
* Physical resource consumption (Gates for Alice/Bob).
* Execution latency (Network synchronization overhead).
* Deterministic success rate (Distribution of **1,000 independent shots**).

*Note: Executions that exceed the HPC queue time limits (e.g., 99 hours due to massive state serialization in highly exposed topologies) will be marked as N/A, confirming the operational limits discussed in the paper.*

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
