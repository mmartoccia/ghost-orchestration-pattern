#!/usr/bin/env python3
"""
Minimal Task Orchestration Daemon

A minimal working skeleton of the Task Loop (Layer 2, Section 2a).

This is NOT production code — it demonstrates the pattern only.
Adapt to your stack: swap the in-memory task store for your database,
swap print() for your notification system, etc.

Run: python3 minimal_daemon.py

Exit: Ctrl+C or send SIGTERM.
"""

import json
import time
import signal
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Task Store (replace with your DB) ──────────────────────────
tasks: dict[str, dict] = {}
TASK_FILE = Path("tasks.json")

# ── Orchestration Log ──────────────────────────────────────────
LOG_FILE = Path("orchestration.log.jsonl")

def log_event(task_id: str, from_state: str, to_state: str, actor: str, **kwargs):
    """Write an immutable JSONL entry BEFORE any other side effects."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "task": task_id,
        "from": from_state,
        "to": to_state,
        "actor": actor,
        **kwargs,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

# ── Signal Handling ─────────────────────────────────────────────
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    print(f"\n[daemon] Received signal {signum}. Finishing current task, then exiting.")
    shutdown_requested = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ── Task Schema ────────────────────────────────────────────────
@dataclass
class Task:
    id: str
    title: str
    status: str  # backlog | ready | in-progress | blocked | done | escalated
    owner: str
    priority: int  # 0=critical, 1=high, 2=medium, 3=low
    blockers: list[str]
    staled_threshold: int = 172800  # seconds

    def to_dict(self):
        return asdict(self)

PRIO = {"critical": 0, "high": 1, "medium": 2, "low": 3}

def load_tasks():
    global tasks
    if TASK_FILE.exists():
        raw = json.loads(TASK_FILE.read_text())
        tasks = {tid: Task(**t) for tid, t in raw.items()}

def save_tasks():
    TASK_FILE.write_text(json.dumps({tid: t.to_dict() for tid, t in tasks.items()}, indent=2))

# ── Core Loop ──────────────────────────────────────────────────
HEARTBEAT_FILE = Path("daemon-heartbeat.json")
EXCLUDE_OWNERS = {"human", "team"}

def write_heartbeat(current_task: Optional[str]):
    HEARTBEAT_FILE.write_text(json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(),
        "pid": __import__("os").getpid(),
        "current_task": current_task,
    }, indent=2))

def pick_next() -> Optional[Task]:
    """Select the highest-priority eligible task."""
    load_tasks()

    # 1. Check for stale in-progress tasks (restart eligible)
    now = time.time()
    for tid, task in tasks.items():
        if task.status == "in-progress":
            started = task.__dict__.get("_started_at", now)
            if now - started > task.staled_threshold:
                print(f"[daemon] Task {tid} stalled (>{task.staled_threshold}s). Escalating.")
                update_status(tid, "escalated", actor="daemon")
                return None

    # 2. Any task already in-progress? (WIP=1 constraint)
    for task in tasks.values():
        if task.status == "in-progress":
            return None

    # 3. Pick highest-priority ready task
    ready = [t for t in tasks.values() if t.status == "ready"]
    if not ready:
        return None

    ready.sort(key=lambda t: (t.priority, t.id))
    return ready[0]

def execute_task(task: Task) -> dict:
    """Execute a task. Returns {ok, result, error}."""
    print(f"[daemon] Executing {task.id}: {task.title}")

    # ── INSERT YOUR EXECUTION LOGIC HERE ──────────────────────────
    # Examples:
    #   result = subprocess.run(["npm", "test"], capture_output=True, timeout=120)
    #   result = spawn_subagent(task)
    #   result = dispatch_to_worker(task)
    # ──────────────────────────────────────────────────────────────

    # Minimal simulation for demo purposes
    time.sleep(0.5)  # pretend work
    return {"ok": True, "result": "done"}

def mark_done(task: Task, result: dict):
    update_status(task.id, "done", actor="daemon", duration_ms=int(time.time() * 1000))

def retry_or_escalate(task: Task, result: dict, retries=0):
    if retries < 2:
        delay = 30 * (2 ** retries)
        print(f"[daemon] {task.id} failed, retrying in {delay}s (attempt {retries + 1}/2)")
        time.sleep(delay)
        # Would re-execute here in production
        update_status(task.id, "ready", actor="daemon")
    else:
        print(f"[daemon] {task.id} exhausted retries. Escalating.")
        update_status(task.id, "escalated", actor="daemon", error=str(result.get("error")))

def update_status(task_id: str, new_status: str, actor: str, **kwargs):
    """Update task status — writes log FIRST, then updates state."""
    load_tasks()
    if task_id not in tasks:
        return

    task = tasks[task_id]
    old_status = task.status

    # Log FIRST (before state change)
    log_event(task_id, old_status, new_status, actor, **kwargs)

    # Update state
    task.status = new_status
    if new_status == "in-progress":
        task._started_at = time.time()
    save_tasks()

    # Check handoff protocol
    if new_status == "done" and task.blockers:
        for blocked_id in task.blockers:
            if blocked_id in tasks and tasks[blocked_id].status == "blocked":
                log_event(blocked_id, "blocked", "ready", "orchestrator",
                          unblocked_by=task_id)
                tasks[blocked_id].status = "ready"
        save_tasks()

    print(f"[daemon] {task_id}: {old_status} → {new_status}")

# ── Main Loop ──────────────────────────────────────────────────
def run():
    print("[daemon] Starting task loop. PID:", __import__("os").getpid())
    print("[daemon] Logs: orchestration.log.jsonl | Heartbeat: daemon-heartbeat.json")
    print("[daemon] Press Ctrl+C to stop.\n")

    iteration = 0
    while not shutdown_requested:
        iteration += 1
        task = pick_next()

        if task is None:
            write_heartbeat(None)
            time.sleep(30)
            continue

        write_heartbeat(task.id)

        result = execute_task(task)
        if result.get("ok"):
            mark_done(task, result)
        else:
            retry_or_escalate(task, result, retries=0)

    print("[daemon] Shutdown complete.")

# ── Demo Seed Data ─────────────────────────────────────────────
def seed_demo_tasks():
    """Create demo tasks if none exist."""
    if TASK_FILE.exists():
        return

    demo_tasks = {
        "DEMO-001": Task(
            id="DEMO-001",
            title="Demo: high-priority ready task",
            status="ready",
            owner="lane-product",
            priority=1,
            blockers=[],
        ),
        "DEMO-002": Task(
            id="DEMO-002",
            title="Demo: blocked task, waiting on DEMO-001",
            status="blocked",
            owner="lane-data",
            priority=2,
            blockers=["DEMO-001"],
        ),
        "DEMO-003": Task(
            id="DEMO-003",
            title="Demo: low-priority backlog task",
            status="backlog",
            owner="lane-strategy",
            priority=3,
            blockers=[],
        ),
    }

    global tasks
    tasks = demo_tasks
    save_tasks()
    print("[daemon] Seeded demo tasks.")

if __name__ == "__main__":
    seed_demo_tasks()
    run()
