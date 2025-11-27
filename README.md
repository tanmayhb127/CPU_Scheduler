# AI CPU Scheduler

A machine learning-based CPU scheduling simulator that uses Imitation Learning to approximate optimal scheduling policies (like SRTF) and compares them against traditional algorithms (Round Robin, SJF, Priority, FCFS).

## Features

- **Imitation Learning**: Trains a Random Forest classifier to mimic the decision-making of an Oracle scheduler (SRTF).
- **Simulation Environment**: Custom CPU environment to model process arrivals, bursts, and execution.
- **Web Interface**: Fast API backend with a frontend dashboard to visualize scheduling timelines and metrics.
- **Metrics**: Calculates Average Waiting Time, Turnaround Time, Response Time, and Deadline Miss Rate.
- **Comparison**: Side-by-side comparison of Learned policy vs. SRTF, SJF, Round Robin, and Priority scheduling.

## Project Structure

- `app.py`: FastAPI backend server for the web and API endpoints.
- `cpu_env.py`: Core simulation logic, `Process` dataclass, and workload generation.
- `train_imitation.py`: Script to generate datasets and train the Random Forest model.
- `run_learned_scheduler.py`: Utility to run simulations using the trained model.
- `models/`: Directory where trained models (`scheduler_imitation.pkl`) are saved.
- `frontend/`: HTML frontend for visualization.

## Getting Started

### Prerequisites

- Python 3.8+
- Dependencies: `fastapi`, `uvicorn`, `pandas`, `numpy`, `scikit-learn`, `joblib`

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/tanmayhb127/CPU_Scheduler.git
    cd CPU_Scheduler
    ```

2.  Install dependencies:
    ```bash
    pip install fastapi uvicorn pandas numpy scikit-learn joblib
    ```

### Usage

1.  **Train the Model**:
    ```bash
    python train_imitation.py
    ```
    This will generate training data and save the model to `models/scheduler_imitation.pkl`.

2.  **Run the Web App**:
    ```bash
    uvicorn app:app --reload
    ```
    Open your browser to `http://127.0.0.1:8000`.

3.  **Simulate**:
    Use the web interface to generate workloads and compare the "Learned" scheduler against traditional policies.

## Development History

Development spanned from May 2025 to November 2025, focusing on building the custom environment, implementing heuristics, gathering training data, and finalizing the web visualization.
