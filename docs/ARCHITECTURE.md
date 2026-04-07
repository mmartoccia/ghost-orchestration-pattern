# Three-Layer Task Orchestration — Architecture

**Pattern version:** 1.0  
**Status:** Production-proven

---

## Overview

The pattern decomposes any automated task execution system into three layers:

1. **Board** — Human-facing work intake, visibility, and triage
2. **Orchestration** — Machine execution engine (self-directing within policy)
3. **Data** — Canonical sources, transforms, and derived stores

The separation is intentional: humans and machines have different latency tolerances, different failure modes, and different access patterns. Forcing them into the same layer is what causes automation to fail.

---

## Layer 1 — Board

**Purpose:** Human work intake, visibility, and escalation. Humans decide what matters; this layer is read-only for machines.

### Components

**Topic Lanes**  
Categorized work queues. Each lane maps to a team, agent, or urgency class. Tasks enter a lane via human intake (triage, ticket, direct assignment). Machines write results back here.

**Dashboard**  
Read-only view of current state: running tasks, blocked tasks, recent completions. Humans check this instead of polling logs or Slack.

**Human Triage + Escalation**  
Humans can:
- Create, update, or close tasks
- Change lane ownership
- Escalate or de-escalate priority
- Halt automated work

Machines can:
- Read task state
- Write execution results
- Write status updates
- Write blocker notifications

### Task Schema

```yaml
id: TASK-001                     # unique, immutable once assigned
uid: 01KXXXXXXXXXXXXXXXX         # human-readable, versioned
title: "Short description"
status: in-progress              # backlog | ready | in-progress | blocked | done | escalated
owner: lane-product              # lane that owns this task
priority: high                   # critical | high | medium | low

# Blocking graph
blockers:
  - id: TASK-000
    owner: lane-data
    reason: "Needs data pipeline completed before this can start"
    requiredOutcome: "Pipeline delivering data to store X"
    resolved: false

# Downstream dependents
downstreamDependents:
  - TASK-003
  - TASK-004

# Auto-handoff when this task completes
handoffProtocol:
  from: lane-data
  to: lane-product
  trigger: status == done
  notification: "TASK-001 done. lane-product: your dependency is resolved."

# Escalation thresholds (lane-aware, see SLA.md)
staledThreshold: 172800          # seconds (48h default)
startedAt: '2026-04-07T12:00:00Z'
updatedAt: '2026-04-07T12:00:00Z'

# Tags for filtering
tags: [enrichment, api, lane-product]
```

---

## Layer 2 — Orchestration

**Purpose:** Automated execution engine. Runs continuously, picks work, executes, logs, and loops.

### 2a. Task Loop (Daemon)

Continuous loop — no cron, no scheduling, just "always running":

```python
while True:
    task = pick_next()          # highest priority, eligible task
    if task is None:            # nothing ready
        sleep(30)               # back off before retry
        continue

    result = execute_task(task)  # run, spawn sub-agent, or dispatch

    if result.ok:
        mark_done(task, result)
    else:
        retry_or_escalate(task, result)
```

**Key properties:**

- **WIP=1**: Only one task in-flight at a time. Eliminates race conditions, simplifies state.
- **Retry with backoff**: 2 retries, exponential backoff (30s → 60s → 120s). Prevents hammering a broken task.
- **Safety skips**: Tasks with `owner=human`, `owner=team`, or marked `executor=human` are never auto-promoted.
- **Heartbeat**: Writes a heartbeat file every loop iteration. External monitors can alert if heartbeat goes stale.
- **Signal handling**: SIGTERM/SIGINT finish the current task cleanly, then exit. No orphaned state.

**pick_next() logic:**
```
1. Check for stale in-progress task (restart eligible, beyond staledThreshold)
2. Check for any task already in-progress (WIP=1 constraint)
3. Otherwise: promote highest-priority backlog task
4. Skip: excluded IDs, human-owned tasks, blocked tasks
```

### 2b. Cron Scheduler

Runs on a fixed interval (typically every 15 minutes):

```
Every N minutes:
  1. Collect system metrics (queue depth, error rate, latency)
  2. Analyze recent work outputs (quality signal, cost signal)
  3. Evaluate against quality rubric
  4. Generate proposals if deviations found
  5. Write to orchestration log
  6. (optional) Push proposals to Board for human review
```

The scheduler does NOT execute tasks. It observes and proposes. Execution always goes through the Task Loop.

**Lane-aware SLA enforcement:** If a task exceeds its lane-specific SLA without visible motion, the scheduler escalates (marks `status: escalated` + notifies the lane owner).

### 2c. Spec Competition (Optional)

For decision-heavy work where multiple approaches should be evaluated before committing:

```
Task enters spec competition:
  1. Policy score: does this task pass the focus/block thresholds?
  2. Pass → queue. Fail → rejected (with reason logged)

Competition round:
  - Agent A (model X) writes spec independently
  - Agent B (model Y) writes spec independently
  - Reviewer scores both against rubric
  - Winner → dispatch to workers
  - ELO rating updated for both agents

Result:
  - Pass → ready-specs (approved builds)
  - Fail → spec-results (with feedback for next round)
```

This is optional. Most implementations don't need multi-agent spec competition. It adds significant overhead.

### 2d. Lane Workers

Background processors, one per lane:

- Each worker watches its assigned lane for new work
- Workers write results back to the Board
- Workers emit progress events to the orchestration log
- Workers handle their own retry within the lane

Workers are lightweight: they don't have the full daemon loop. They're triggered by the scheduler or by board state changes.

---

## Layer 3 — Data

**Purpose:** Canonical sources, ETL/sync pipelines, and derived stores.

### Producer / Canonical Source

The authoritative data store. Rules:
- **Read-only for consumers.** Orchestration never writes back to the canonical source.
- **Append-only where possible.** Makes sync idempotent and audit-friendly.
- **Schema versioning required.** Maintain a `schema_version` table with compatibility level.

```sql
CREATE TABLE schema_version (
    version TEXT PRIMARY KEY,
    compatibility_level INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    schema_hash_sha256 TEXT
);
```

Consumer ETL must read this table and refuse to run if `compatibility_level > MAX_SUPPORTED`.

### ETL / Sync Pipeline

Moves and transforms data from canonical source to the execution environment:

- **Scheduled sync**: rsync, cron, or event-driven depending on the source
- **Schema validation**: validate against consumer's `MAX_SUPPORTED` before ingesting
- **Enrichment**: add derived fields, join with other sources, filter noise
- **Idempotency**: same sync run should produce same result (use deterministic keys)

### Derived Store

The queryable layer the orchestration system actually reads from:

- PostgreSQL, SQLite, or equivalent
- Tables are materializations of canonical source + business logic
- **Always treat as derived.** Can be rebuilt from canonical source.
- **Read by orchestration.** Written only by the ETL/sync pipeline.

---

## The Orchestration Log

Every state change is written to an **immutable append-only JSONL file** before any notification fires.

```jsonl
{"ts": "2026-04-07T12:00:00Z", "task": "TASK-001", "from": "ready", "to": "in-progress", "actor": "daemon", "duration_ms": 0}
{"ts": "2026-04-07T12:00:08Z", "task": "TASK-001", "from": "in-progress", "to": "done", "actor": "daemon", "duration_ms": 8420}
{"ts": "2026-04-07T12:00:09Z", "task": "TASK-002", "from": "blocked", "to": "ready", "actor": "orchestrator", "unblocked_by": "TASK-001"}
```

**Why log-first?** If notifications fail (webhook down, Telegram blocked), the log is already committed. The system is never in a state where work changed but nobody knows.

**Log schema fields:**
- `ts` — ISO 8601 UTC timestamp
- `task` — Task ID
- `from` — Previous state
- `to` — New state
- `actor` — What triggered the change (`daemon`, `scheduler`, `worker`, `human`)
- `duration_ms` — Execution time (for completion events)
- `unblocked_by` — Which task resolved the blocker (for unblock events)

---

## Escalation Logic

See [SLA.md](SLA.md) for the full lane-aware escalation matrix.

**Core rule:** Not all work decays at the same rate. A stale data pipeline is more dangerous than a stale strategy document. Use lane-aware urgency instead of a flat "escalate after X hours" rule.

**Motion signal rule:** Silent ownership does not count as progress. Visible motion means:
- Task status explicitly updated
- Blocker state changed
- Heartbeat/lease refreshed with matching board update

---

## API Reference

The orchestration engine exposes a simple REST API:

```
GET  /tasks                    List tasks (filter: ?owner=X&status=Y)
GET  /tasks/{id}               Get task details
GET  /tasks/{id}/blockers      Get blocking tasks + owners
GET  /tasks/{id}/dependents    Get downstream dependents
POST /tasks/{id}/status        Update status (triggers handoffs, writes log)
GET  /orchestration/handoffs   Pending handoffs + recent activity
```

All state mutations write the orchestration log before returning. Notifications fire after the log is committed.

---

## File Structure

```
.
├── README.md                   # This file
├── docs/
│   ├── ARCHITECTURE.md          # This document
│   ├── SLA.md                   # Lane-aware SLA/escalation matrix
│   └── ORCHESTRATION_LOG.md     # JSONL log schema reference
├── diagrams/
│   ├── ARCHITECTURE.mmd         # 3-layer system overview
│   ├── TASK_LOOP.mmd            # Daemon loop flow
│   ├── SPEC_COMPETITION.mmd     # Optional multi-agent decision mode
│   └── DATA_LAYER.mmd           # Producer/sync/consumer flow
├── examples/
│   ├── minimal_daemon.py        # Minimal working daemon skeleton
│   ├── task_schema.yaml          # Full task schema with all fields
│   └── schema.json              # JSONL orchestration log schema
└── src/                         # (optional) reference implementations
```
