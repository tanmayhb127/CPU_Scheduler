# train_imitation.py
import numpy as np
import pandas as pd
from typing import List
from cpu_env import Process, generate_workload
import joblib, os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

def build_dataset(n_workloads=400, seed=7, oracle_policy="srtf"):
    rng = np.random.default_rng(seed)
    rows = []
    for wid in range(n_workloads):
        base = generate_workload(n= int(rng.integers(6,14)), seed= int(seed+wid), lam= float(rng.uniform(4,10)))
        # fresh copy
        sim_procs = [Process(pid=p.pid, arrival=p.arrival, burst=p.burst, priority=p.priority) for p in base]
        t = 0
        ready = []
        running = None
        while any(p.remaining>0 for p in sim_procs) and t<10000:
            # arrivals
            for p in sim_procs:
                if p.arrival == t:
                    ready.append(p)

            if ready or running:
                candidates = ready + ([running] if running and running.remaining>0 else [])
                # oracle pick
                if oracle_policy == "srtf":
                    target = min(candidates, key=lambda p: p.remaining).pid
                elif oracle_policy == "priority":
                    target = min(candidates, key=lambda p: p.priority).pid
                else:
                    target = min(candidates, key=lambda p: p.remaining).pid

                for p in candidates:
                    rows.append({
                        "wid": wid,
                        "time": t,
                        "pid": p.pid,
                        "arrival": p.arrival,
                        "burst": p.burst,
                        "priority": p.priority,
                        "remaining": p.remaining,
                        "wait": max(0, t - p.arrival) if p.arrival <= t else -1,
                        "label": 1 if p.pid == target else 0,
                        "num_ready": len(candidates),
                    })

                # step according to oracle
                choose = None
                if oracle_policy == "srtf":
                    choose = min(candidates, key=lambda p: p.remaining)
                elif oracle_policy == "priority":
                    choose = min(candidates, key=lambda p: p.priority)
                else:
                    choose = min(candidates, key=lambda p: p.remaining)
                if choose is not running and running and running.remaining>0:
                    ready.append(running)
                if choose in ready: ready.remove(choose)
                running = choose
                if running.first_response_time is None:
                    running.first_response_time = t
                running.remaining -= 1
                if running.remaining == 0:
                    running = None

            t += 1

    df = pd.DataFrame(rows)
    df = df[df["wait"] >= 0].reset_index(drop=True)
    return df

def train_and_save(df: pd.DataFrame, outpath="models/scheduler_imitation.pkl"):
    X = df[["arrival","burst","priority","remaining","wait","num_ready"]]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("F1:", f1_score(y_test, y_pred))
    print(classification_report(y_test, y_pred, digits=3))

    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, outpath)
    print("Saved:", outpath)

if __name__ == "__main__":
    df = build_dataset(n_workloads=500, seed=11, oracle_policy="srtf")  # change oracle_policy to teach other behaviors
    print(df.head())
    train_and_save(df)
