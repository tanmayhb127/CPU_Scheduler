# app.py
import os
import io
import csv
import json
import joblib
from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import pandas as pd

from cpu_env import generate_workload, simulate, Process

app = FastAPI(title="AI CPU Scheduler Simulator")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Try to load model if present
MODEL_PATH = os.getenv("MODEL_PATH", "models/scheduler_imitation.pkl")
_model = None
if os.path.exists(MODEL_PATH):
    try:
        _model = joblib.load(MODEL_PATH)
        print("[INFO] Loaded model:", MODEL_PATH)
    except Exception as e:
        print("[WARN] Could not load model:", e)


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve a single-file frontend (built-in)"""
    html = open("frontend/index.html", "r", encoding="utf-8").read()
    return HTMLResponse(content=html, status_code=200)

@app.post("/api/generate")
async def api_generate(n: int = Form(12), seed: int = Form(0)):
    procs = generate_workload(n=n, seed=seed)
    rows = [{"pid": p.pid, "arrival": p.arrival, "burst": p.burst, "priority": p.priority} for p in procs]
    return {"workload": rows}

@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """Accept CSV or JSON workload file.
    CSV columns: pid,arrival,burst,priority (priority optional)
    JSON: array of objects with same keys
    """
    content = await file.read()
    text = content.decode("utf-8")
    rows = []
    if file.filename.lower().endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        for r in reader:
            rows.append({
                "pid": int(r.get("pid")),
                "arrival": int(r.get("arrival")),
                "burst": int(r.get("burst")),
                "priority": int(r.get("priority") or 0)
            })
    else:
        data = json.loads(text)
        for r in data:
            rows.append({
                "pid": int(r.get("pid")),
                "arrival": int(r.get("arrival")),
                "burst": int(r.get("burst")),
                "priority": int(r.get("priority") or 0)
            })
    return {"workload": rows}

def run_model_scheduler(procs, model):
    import pandas as pd
    # simple wrapper: at each tick pick candidate with max model.score (predict_proba for label=1)
    procs_copy = [Process(pid=p["pid"], arrival=p["arrival"], burst=p["burst"], priority=p.get("priority",0)) for p in procs]
    # Simulate similarly to simulate_learned in notebook, but inline
    t = 0
    timeline = []
    ready = []
    running = None
    max_time = 10000
    while t < max_time and any(p.remaining>0 for p in procs_copy):
        for p in procs_copy:
            if p.arrival == t:
                ready.append(p)
        if ready or running:
            candidates = ready + ([running] if running and running.remaining>0 else [])
            # build features
            feats = []
            for p in candidates:
                feats.append([p.arrival, p.burst, p.priority, p.remaining, max(0, t - p.arrival), len(candidates)])
            import numpy as np
            X = pd.DataFrame(feats, columns=["arrival","burst","priority","remaining","wait","num_ready"])
            probs = model.predict_proba(X)[:,1]
            idx = int(probs.argmax())
            choose = candidates[idx]
            if choose is not running:
                if running and running.remaining>0:
                    ready.append(running)
                if choose in ready:
                    ready.remove(choose)
                running = choose
                if running.first_response_time is None:
                    running.first_response_time = t
        if running:
            running.remaining -= 1
            timeline.append((t, running.pid))
            if running.remaining == 0:
                running.completion = t+1
                running = None
        else:
            timeline.append((t, -1))
        t += 1
    metrics = {}
    from cpu_env import compute_metrics
    metrics = compute_metrics(procs_copy, timeline)
    res = {"timeline": [{"t": t, "pid": pid} for t, pid in timeline], "metrics": metrics, "procs": [{"pid":p.pid,"arrival":p.arrival,"burst":p.burst,"priority":p.priority,"completion":p.completion} for p in procs_copy]}
    return res

@app.post("/api/simulate")
async def api_simulate(payload: Dict[str, Any]):
    """
    POST body:
    {
      "workload": [{"pid":0,"arrival":0,"burst":5,"priority":0}, ...],
      "policy": "srtf"|"sjf"|"priority"|"rr"|"learned",
      "time_quantum": 1
    }
    """
    workload = payload.get("workload")
    policy = payload.get("policy", "srtf")
    time_quantum = int(payload.get("time_quantum", 1))

    if not workload:
        return JSONResponse({"error":"no workload provided"}, status_code=400)

    # convert to Process list
    procs = [Process(pid=int(p["pid"]), arrival=int(p["arrival"]), burst=int(p["burst"]), priority=int(p.get("priority",0))) for p in workload]

    if policy == "learned":
        if _model is None:
            return JSONResponse({"error":"learned model not available. Train and place models/scheduler_imitation.pkl first."}, status_code=400)
        res = run_model_scheduler([{"pid":p.pid,"arrival":p.arrival,"burst":p.burst,"priority":p.priority} for p in procs], _model)
        return res
    else:
        sim = simulate(procs, policy=policy, time_quantum=time_quantum)
        return {"timeline": [{"t": t, "pid": pid} for t,pid in sim.timeline], "metrics": sim.metrics, "procs": [{"pid":p.pid,"arrival":p.arrival,"burst":p.burst,"priority":p.priority,"completion":p.completion} for p in sim.procs]}

@app.get("/api/modelinfo")
async def model_info():
    return {"model_loaded": _model is not None, "model_path": MODEL_PATH}
