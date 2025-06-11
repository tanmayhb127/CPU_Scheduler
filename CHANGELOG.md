[2025-05-01 17:45:00] Initial project setup and directory structure
[2025-05-03 09:41:00] Define Process dataclass in cpu_env.py
[2025-05-05 16:04:00] Implement __post_init__ for proper field initialization in Process
[2025-05-08 13:42:00] Draft generation of workload with exponential distribution
[2025-05-10 13:14:00] Add random seeding to workload generation for reproducibility
[2025-05-13 15:54:00] Refactor generate_workload to support variable arrival times
[2025-05-15 13:51:00] Add priority field to Process class
[2025-05-18 14:58:00] Implement Priority generation logic in workload
[2025-05-20 16:19:00] Create CPUSimResult class to hold simulation metrics
[2025-05-23 12:19:00] Outline compute_metrics function signature
[2025-05-25 17:13:00] Implement average waiting time calculation
[2025-05-27 10:14:00] Add average turnaround time calculation
[2025-05-30 11:20:00] Add response time metric to compute_metrics
[2025-06-01 15:50:00] Implement deadline miss rate calculation
[2025-06-04 13:34:00] Fix division by zero bug in metrics when n=0
[2025-06-06 14:33:00] Define pick_srtf heuristic function
[2025-06-09 10:12:00] Implement Shortest Remaining Time First logic
[2025-06-11 17:01:00] Define pick_sjf heuristic function
