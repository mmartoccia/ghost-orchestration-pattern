# Three-Layer Task Orchestration Pattern

A production-proven architecture for running multi-agent task execution with human oversight.

**Core principle:** Humans define what matters. Machines decide what moves next.

---

## The Problem

Most automation fails at the human/machine boundary:
- Machines execute but humans don't know what's happening
- Humans get involved too often, creating bottlenecks
- No clear contract for when machines can self-direct vs. when to escalate
- Tool sprawl: cron jobs, scripts, agents all running independently with no shared state

## The Solution

Three cleanly separated layers:

```
Layer 1: BOARD          Human-facing work intake, visibility, triage
Layer 2: ORCHESTRATION  Automated execution engine
Layer 3: DATA           Canonical sources, transforms, derived stores
```

**Key design rule:** Humans own what matters (policy, priorities, escalation). Machines own what moves (task picking, execution, retry, logging).

---

## Quick Start

```bash
# 1. Start the daemon
python3 examples/minimal_daemon.py

# 2. Watch the log
tail -f orchestration.log.jsonl
```

---

## Architecture Diagrams

### Full Architecture

```mermaid
graph TB
    subgraph BOARD["LAYER 1 - BOARD"]
        INTAKE["Human work intake + Triage"]
        LANES["fast-lane / medium-lane / slow-lane"]
        INC["incident-board.md"]
        INTAKE --> LANES
        LANES --> INC
    end
    subgraph ORCH["LAYER 2 - ORCHESTRATION"]
        DAEMON["Task Loop Daemon"]
        CRONJ["Cron Scheduler 15min TASTE"]
        SPEC["Spec Competition ELO"]
        WORKERS["Lane Workers"]
        OLOG["orchestration.log.jsonl"]
        DAEMON -.-> OLOG
        CRONJ -.-> OLOG
    end
    subgraph DATA["LAYER 3 - DATA"]
        CANON["Canonical Source append-only"]
        ETL["ETL Sync schema validation"]
        STORE["Derived Store PostgreSQL SQLite"]
        CANON --> ETL --> STORE
    end
    BOARD --> ORCH
    ORCH --> DATA
```

---

### Board Layer

```mermaid
graph TD
    SIG["Inbound Signals - Telegram / Email / Cron / Alert"] --> TRIAGE["Human Triage - choose lane and priority"]
    TRIAGE --> FL["fast-lane.md - Product / API"]
    TRIAGE --> ML["medium-lane.md - Data / ETL"]
    TRIAGE --> SL["slow-lane.md - Strategy"]
    TRIAGE --> IB["incident-board.md - cross-lane"]
    FL --> TG6["Telegram Topic 6"]
    ML --> TG5["Telegram Topic 5"]
    SL --> TG3["Telegram Topic 3"]
    IB --> TG1["Telegram Topic 1"]
```

### Lane Workers

```mermaid
graph TD
    LANE["lane.md - task blocks"] --> POLL
    POLL --> LANE
    POLL["poll_lane() - check for ready tasks"] --> SORT["Sort by priority - pick next task"]
    SORT --> EXEC["execute task - do the work"]
    EXEC --> WRITE["write_result() - update Board"]
    WRITE --> POLL
    WRITE --> TW1["Fast Worker - 30-60s cycle"]
    WRITE --> TW2["Medium Worker - 2-5 min cycle"]
    WRITE --> TW3["Slow Worker - 5-15 min cycle"]
    WRITE -.-> HB["worker.json - Heartbeat"]
    HB -.-> SUP["Supervisor - auto-restart"]
```

### Orchestration API

```mermaid
graph TD
    CL1["Daemon"] --> API
    CL2["Worker"] --> API
    CL3["Human"] --> API
    CL4["Cron"] --> API
    subgraph API["ORCHESTRATION API /api"]
        EP1["GET /tasks"]
        EP2["GET /tasks/id/blockers"]
        EP3["GET /tasks/id/dependents"]
        EP4["POST /tasks/id/status"]
        EP5["GET /handoffs"]
    end
    subgraph SEQ["POST atomicity sequence"]
        AT1["1. Write log FIRST"]
        AT2["2. Update task state"]
        AT3["3. Check handoff protocol"]
        AT4["4. Send notification"]
        AT1 --> AT2 --> AT3 --> AT4
    end
    EP4 --> SEQ
```

### Cron Scheduler

```mermaid
graph TD
    TRIGGER["Every 15 minutes"] --> CM1["1. Collect Metrics"]
    CM1 --> CM2["2. Analyze Outputs"]
    CM2 --> CM3["3. Evaluate TASTE Rubric"]
    CM3 --> CM4["4. Generate Proposals"]
    CM4 --> CM5["5. Write JSONL Log"]
    CM5 --> CM6["6. Push to Board"]
    CM3 -.-> TR1["Throughput"]
    CM3 -.-> TR2["Accuracy"]
    CM3 -.-> TR3["Stability"]
    CM3 -.-> TR4["Cost"]
    CM3 -.-> TR5["Evolution"]
    CM4 --> PR1["Throughput - Fast-lane"]
    CM4 --> PR2["Accuracy - Quality"]
    CM4 --> PR3["Stability - Incident"]
    CM4 --> PR4["Cost - Org-wide"]
```

### Spec Competition + ELO

```mermaid
graph TD
    TASK["Task enters competition"] --> GATE["Policy gate - focus and block thresholds"]
    GATE -->|"pass"| QUEUE["task-queue - wait for slot"]
    GATE -->|"fail"| REJECT["rejected"]
    QUEUE --> AGTA["Agent A writes spec"]
    QUEUE --> AGTB["Agent B writes spec"]
    AGTA --> REV["Reviewer scores both - quality x alignment x risk"]
    AGTB --> REV
    REV --> WIN["Winner dispatched"]
    REV --> LOSE["Loser archived"]
    WIN -.->|"ELO up"| ELO1["Agent A rating increases"]
    LOSE -.->|"ELO down"| ELO2["Agent B rating decreases"]
    ELO1 --> ELOF["spec-elo.json"]
    ELO2 --> ELOF
    WIN --> WKRS["Workers execute spec"]
    WKRS --> CBACK["spec-callbacks"]
    CBACK --> JUDGE["Judge evaluates result"]
```

---

## What's Included

| Path | Description |
|------|-------------|
| `docs/ARCHITECTURE.md` | Full architecture doc |
| `docs/SLA.md` | Lane-aware SLA/escalation matrix |
| `diagrams/*.mmd` | Mermaid source files |
| `examples/minimal_daemon.py` | Working skeleton daemon |
| `examples/task_schema.yaml` | Full task schema reference |
| `examples/schema.json` | JSONL orchestration log schema |
| `reference/` | Production-tested implementation patterns |

---

## When to Use This

**Good fits:**
- Multi-agent systems with shared task state
- Ops/runbook automation needing human escalation
- Data pipelines with freshness SLAs
- Any system where humans need visibility without constant involvement

**Bad fits:**
- Pure human workflows (use a kanban board)
- Real-time control systems (loop latency is too high)
- One-off scripts (overhead not worth it)

---

## Reference Implementation Layer

The `reference/` directory contains production-tested implementation patterns:

| File | Description |
|------|-------------|
| `reference/BOARD_LAYER.md` | Coordination boards, topic lanes, incident routing |
| `reference/LANE_WORKERS.md` | Per-lane background processor, startup supervisor, health checks |
| `reference/MC_API.md` | 5-endpoint REST API, atomicity contract, Flask implementation |
| `reference/CRON_ORCHESTRATOR.md` | 15-min scheduler, TASTE rubric, alert routing |
| `reference/SPEC_COMPETITION.md` | Multi-agent ELO rating system, reviewer rubric |

These are **reference patterns**, not drop-in implementations. Adapt to your stack.

---

## Status

Pattern is production-proven. Reference implementations are skeletons.

MIT License.
