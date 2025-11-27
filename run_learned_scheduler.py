# run_learned_scheduler.py
import joblib
import pandas as pd
import numpy as np
from cpu_env import Process, generate_workload, simulate, compute_metrics

def pick_with_model(model, candidates, t):
    feats = pd.DataFrame([{
        "arrival": p.arrival,
        "burst": p.burst,
        "priority": p.priority,
        "remaining": p.remaining,
        "wait": max(0, t - p.arrival),
        "num_ready": len(candidates)
    } for p in candidates])
    probs = model.predict_proba(feats)[:,1]
    j = int(probs.argmax())
    return candidates[j]

def simulate_learned(procs_in, model, max_time=10000):
    procs = [Process(pid=p.pid, arrival=p.arrival, burst=p.burst, priority=p.priority) for p in procs_in]
    t = 0
    timeline = []
    ready = []
    running = None

    while (t<max_time) and any(p.remaining>0 for p in procs):
        for p in procs:
            if p.arrival == t: ready.append(p)

        if ready or running:
            candidates = ready + ([running] if running and running.remaining>0 else [])
            choose = pick_with_model(model, candidates, t)
            if choose is not running:
                if running and running.remaining>0:
                    ready.append(running)
                if choose in ready: ready.remove(choose)
                running = choose
                if running.first_response_time is None:
                    running.first_response_time = t

        if running:
            running.remaining -= 1
            if running.remaining == 0:
                running.completion = t+1
                running = None
            timeline.append((t, running.pid if running else -1))
        else:
            timeline.append((t, -1))
        t += 1

    metrics = compute_metrics(procs, timeline)
    return timeline, metrics

if __name__ == "__main__":
    # Train first via `python train_imitation.py` so models/scheduler_imitation.pkl exists.
    model_path = "models/scheduler_imitation.pkl"
    model = joblib.load(model_path)

    procs = generate_workload(n=12, seed=123, lam=7)
    learned_tl, learned_metrics = simulate_learned(procs, model)
    srtf_res = simulate(procs, policy="srtf")
    sjf_res  = simulate(procs, policy="sjf")
    prio_res = simulate(procs, policy="priority")
    rr_res   = simulate(procs, policy="rr", time_quantum=2)

    print("Learned:", learned_metrics)
    print("SRTF   :", srtf_res.metrics)
    print("SJF    :", sjf_res.metrics)
    print("PRIOR  :", prio_res.metrics)
    print("RR(q=2):", rr_res.metrics)
