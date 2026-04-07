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
graph TD
    L1[Layer 1 Board]
    B1[Human intake and triage]
    B2[Topic lanes]
    B3[Incident board]
    L2[Layer 2 Orchestration]
    O1[Task loop daemon]
    O2[Cron scheduler]
    O3[Spec competition]
    O4[Lane workers]
    O5[Orchestration log]
    L3[Layer 3 Data]
    D1[Canonical source]
    D2[ETL sync]
    D3[Derived store]

    L1 --> B1 --> B2 --> B3
    L1 --> L2
    L2 --> O1
    L2 --> O2
    L2 --> O3
    L2 --> O4
    O1 --> O5
    O2 --> O5
    L2 --> L3
    L3 --> D1 --> D2 --> D3
```

---

### Board Layer

```mermaid
graph TD
    S1[Inbound signals]
    S2[Human triage]
    S3[Fast lane]
    S4[Medium lane]
    S5[Slow lane]
    S6[Incident board]
    T1[Topic 6]
    T2[Topic 5]
    T3[Topic 3]
    T4[Topic 1]

    S1 --> S2
    S2 --> S3
    S2 --> S4
    S2 --> S5
    S2 --> S6
    S3 --> T1
    S4 --> T2
    S5 --> T3
    S6 --> T4
```

### Lane Workers

```mermaid
graph TD
    W1[Lane file]
    W2[Poll lane]
    W3[Pick next task]
    W4[Execute task]
    W5[Write result]
    W6[Fast worker]
    W7[Medium worker]
    W8[Slow worker]
    W9[Worker heartbeat]
    W10[Supervisor]

    W1 --> W2 --> W3 --> W4 --> W5 --> W2
    W5 --> W6
    W5 --> W7
    W5 --> W8
    W5 --> W9 --> W10
```

### Orchestration API

```mermaid
graph TD
    C1[Daemon]
    C2[Worker]
    C3[Human]
    C4[Cron]
    A1[Orchestration API]
    E1[Get tasks]
    E2[Get blockers]
    E3[Get dependents]
    E4[Post task status]
    E5[Get handoffs]
    Q1[Write log first]
    Q2[Update task state]
    Q3[Check handoff]
    Q4[Send notification]

    C1 --> A1
    C2 --> A1
    C3 --> A1
    C4 --> A1
    A1 --> E1
    A1 --> E2
    A1 --> E3
    A1 --> E4
    A1 --> E5
    E4 --> Q1 --> Q2 --> Q3 --> Q4
```

### Cron Scheduler

```mermaid
graph TD
    R1[Every 15 minutes]
    R2[Collect metrics]
    R3[Analyze outputs]
    R4[Evaluate TASTE rubric]
    R5[Generate proposals]
    R6[Write JSONL log]
    R7[Push to board]
    T1[Throughput]
    T2[Accuracy]
    T3[Stability]
    T4[Cost]
    T5[Evolution]
    P1[Fast lane proposal]
    P2[Quality proposal]
    P3[Incident proposal]
    P4[Org wide proposal]

    R1 --> R2 --> R3 --> R4 --> R5 --> R6 --> R7
    R4 --> T1
    R4 --> T2
    R4 --> T3
    R4 --> T4
    R4 --> T5
    R5 --> P1
    R5 --> P2
    R5 --> P3
    R5 --> P4
```

### Spec Competition + ELO

```mermaid
graph TD
    S1[Task enters competition]
    S2[Policy gate]
    S3[Queue]
    S4[Reject]
    S5[Agent A writes spec]
    S6[Agent B writes spec]
    S7[Reviewer scores both]
    S8[Winner dispatched]
    S9[Loser archived]
    S10[Agent A rating up]
    S11[Agent B rating down]
    S12[Spec elo file]
    S13[Workers execute spec]
    S14[Callback]
    S15[Judge result]

    S1 --> S2
    S2 --> S3
    S2 --> S4
    S3 --> S5
    S3 --> S6
    S5 --> S7
    S6 --> S7
    S7 --> S8
    S7 --> S9
    S8 --> S10 --> S12
    S9 --> S11 --> S12
    S8 --> S13 --> S14 --> S15
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
