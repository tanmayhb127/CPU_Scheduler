# cpu_env.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import random
import math

@dataclass
class Process:
    pid: int
    arrival: int
    burst: int
    priority: int = 0
    deadline: Optional[int] = None

    # runtime fields
    remaining: int = field(init=False)
    first_response_time: Optional[int] = field(default=None, init=False)
    completion: Optional[int] = field(default=None, init=False)
    last_scheduled_at: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        self.remaining = self.burst

def generate_workload(n:int=10, seed:int=0, burst_dist:str="exp", lam:float=6.0, p_prio:bool=True) -> List[Process]:
    random.seed(seed)
    procs = []
    t = 0
    for i in range(n):
        # arrivals have small gaps
        t += random.randint(0, 3)
        if burst_dist == "exp":
            b = max(1, int(random.expovariate(1/lam)))
        else:
            b = max(1, int(random.gauss(lam, lam/3)))
        pr = random.randint(0, 7) if p_prio else 0
        procs.append(Process(pid=i, arrival=t, burst=b, priority=pr))
    return procs

class CPUSimResult:
    def __init__(self, timeline, metrics):
        self.timeline = timeline  # list of (time, pid) per tick
        self.metrics = metrics    # dict

def compute_metrics(procs: List[Process], timeline: List[Tuple[int,int]]) -> Dict[str, float]:
    # Calculate waiting, turnaround, response time
    n = len(procs)
    wait = 0; tat = 0; resp = 0; missed = 0
    for p in procs:
        completion = p.completion if p.completion is not None else (timeline[-1][0] + 1 if timeline else 0)
        turnaround = completion - p.arrival
        waiting = turnaround - p.burst
        response = (p.first_response_time - p.arrival) if p.first_response_time is not None else 0
        tat += turnaround; wait += waiting; resp += response
        if p.deadline is not None and completion > p.deadline:
            missed += 1
    return {
        "avg_wait": wait / n,
        "avg_tat": tat / n,
        "avg_resp": resp / n,
        "miss_rate": missed / n
    }

# Heuristic baseline policies
def pick_srtf(ready: List[Process]):
    return min(ready, key=lambda p: p.remaining)

def pick_sjf(ready: List[Process]):
    return min(ready, key=lambda p: p.burst)

def pick_priority(ready: List[Process]):
    return min(ready, key=lambda p: p.priority)

def pick_rr(ready: List[Process], rr_index: int):
    return ready[rr_index % len(ready)]

def simulate(procs_in: List[Process], policy="srtf", time_quantum:int=1, max_time:int=10000):
    # Copy to avoid mutating input
    procs = [Process(pid=p.pid, arrival=p.arrival, burst=p.burst, priority=p.priority, deadline=p.deadline) for p in procs_in]
    t = 0
    timeline = []
    rr_idx = 0
    ready: List[Process] = []
    running: Optional[Process] = None
    next_q = 0

    while (t < max_time) and (any(p.remaining > 0 for p in procs)):
        # add arrivals
        for p in procs:
            if p.arrival == t:
                ready.append(p)

        # preemption or selection
        if running is None or (policy in ["srtf", "priority"]):
            if ready:
                if policy == "srtf":
                    cand = pick_srtf(ready + ([running] if running and running.remaining>0 else []))
                elif policy == "priority":
                    cand = pick_priority(ready + ([running] if running and running.remaining>0 else []))
                elif policy == "sjf":
                    cand = pick_sjf(ready) if running is None else running
                elif policy == "rr":
                    cand = pick_rr(ready, rr_idx) if running is None else running
                else:
                    cand = pick_srtf(ready + ([running] if running and running.remaining>0 else []))
                if cand is not running:
                    if running and running.remaining>0:
                        ready.append(running)
                    running = cand
                    ready.remove(cand)
                    next_q = t + time_quantum
                    if running.first_response_time is None:
                        running.first_response_time = t
        else:
            # time quantum expiration for RR/SJF
            if t >= next_q and policy in ["rr", "sjf"]:
                if running and running.remaining>0:
                    ready.append(running)
                    if policy == "rr":
                        rr_idx += 1
                running = None
                continue  # re-loop to pick new

        # execute 1 tick
        if running:
            running.remaining -= 1
            timeline.append((t, running.pid))
            if running.remaining == 0:
                running.completion = t + 1
                running = None
        else:
            timeline.append((t, -1))  # idle
        t += 1

    metrics = compute_metrics(procs, timeline)
    result = CPUSimResult(timeline, metrics)
    result.procs = procs  # attach for inspection
    return result
