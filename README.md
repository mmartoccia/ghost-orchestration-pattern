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
    B0[Layer 1 Board]
    B1[Human intake and triage]
    B2[Topic map, channel to file routing]
    B3[Fast lane, product API user facing]
    B4[Medium lane, data pipeline ETL]
    B5[Slow lane, strategy research]
    B6[Incident board, cross lane escalation]
    B7[Org wide board, governance staffing]

    O0[Layer 2 Orchestration]
    O1[Task loop daemon]
    O2[Pick next task, WIP 1, highest priority]
    O3[Execute task, run spawn dispatch]
    O4[Mark done or blocked, write log before notify]
    O5[Cron scheduler]
    O6[Collect metrics and analyze outputs]
    O7[Evaluate TASTE and generate proposals]
    O8[Spec competition]
    O9[Agent A and Agent B write specs]
    O10[Reviewer scores both and updates ELO]
    O11[Lane workers]
    O12[Fast worker, 30 to 60 seconds]
    O13[Medium worker, 2 to 5 minutes]
    O14[Slow worker, 5 to 15 minutes]

    D0[Layer 3 Data]
    D1[Canonical source, append only for consumers]
    D2[ETL and sync, schema validation]
    D3[Derived store, PostgreSQL or SQLite]

    L0[orchestration log JSONL, immutable append only]
    A0[Orchestration API]
    A1[Get tasks]
    A2[Get blockers and dependents]
    A3[Post task status, atomic log state handoff notify]
    A4[Get handoffs]

    B0 --> B1
    B1 --> B2
    B1 --> B3
    B1 --> B4
    B1 --> B5
    B1 --> B6
    B1 --> B7

    B0 --> O0
    O0 --> O1 --> O2 --> O3 --> O4
    O0 --> O5 --> O6 --> O7
    O0 --> O8 --> O9 --> O10
    O0 --> O11
    O11 --> O12
    O11 --> O13
    O11 --> O14

    O4 --> L0
    O7 --> L0

    O0 --> A0
    A0 --> A1
    A0 --> A2
    A0 --> A3
    A0 --> A4

    O0 --> D0
    D0 --> D1 --> D2 --> D3
    L0 --> B0
```

---

### Board Layer

```mermaid
graph TD
    B1[Work arrival, Telegram email cron human input]
    B2[Human triage, choose lane by primary surface]
    B3[Fast lane, customer facing product API]
    B4[Medium lane, data pipeline ETL]
    B5[Slow lane, strategy research]
    B6[Incident board, cross lane issues]
    B7[Org wide board, governance staffing]
    B8[Topic map, stable channel to file mapping]
    N1[Telegram Topic 6, fast lane events]
    N2[Telegram Topic 5, medium lane events]
    N3[Telegram Topic 3, slow lane events]
    N4[Telegram Topic 1, cross lane incidents]

    B1 --> B2
    B2 --> B3
    B2 --> B4
    B2 --> B5
    B2 --> B6
    B2 --> B7
    B2 --> B8
    B3 --> N1
    B4 --> N2
    B5 --> N3
    B6 --> N4
    B3 --> B6
    B4 --> B6
    B5 --> B6
    B3 --> B7
    B4 --> B7
    B5 --> B7
```

### Lane Workers

```mermaid
graph TD
    W1[Lane file, markdown task blocks]
    W2[Ready blocked done task state]
    W3[Poll lane for ready tasks]
    W4[Sort by priority]
    W5[Pick highest priority task]
    W6[Execute task, API call script or sub agent]
    W7[Write result back to board]
    W8[Worker heartbeat JSON]
    W9[Supervisor checks staleness and restarts]
    W10[Fast lane worker, 30 to 60 seconds]
    W11[Medium lane worker, 2 to 5 minutes]
    W12[Slow lane worker, 5 to 15 minutes]
    W13[Worker registry and pid files]

    W1 --> W2
    W1 --> W3 --> W4 --> W5 --> W6 --> W7 --> W3
    W7 --> W1
    W7 --> W8 --> W9
    W13 --> W10
    W13 --> W11
    W13 --> W12
    W10 --> W3
    W11 --> W3
    W12 --> W3
```

### Orchestration API

```mermaid
graph TD
    C1[Daemon]
    C2[Worker]
    C3[Human dashboard]
    C4[Cron scheduler]
    A0[Orchestration API, slash api]
    A1[Get tasks, owner status priority filters]
    A2[Get task by id]
    A3[Get blockers]
    A4[Get dependents]
    A5[Post task status]
    A6[Get handoffs]
    Q1[Write orchestration log first]
    Q2[Update task state in store]
    Q3[Check handoff protocol and unblock dependents]
    Q4[Send notification after log commit]
    R1[Response with task transition and handoffs]

    C1 --> A0
    C2 --> A0
    C3 --> A0
    C4 --> A0
    A0 --> A1
    A0 --> A2
    A0 --> A3
    A0 --> A4
    A0 --> A5
    A0 --> A6
    A5 --> Q1 --> Q2 --> Q3 --> Q4 --> R1
```

### Cron Scheduler

```mermaid
graph TD
    C1[Every 15 minutes]
    C2[Collect metrics, queue depth error rate throughput cost stall rate]
    C3[Analyze recent outputs, quality signal and cost]
    C4[Evaluate TASTE rubric]
    T1[Throughput]
    T2[Accuracy]
    T3[Stability]
    T4[Cost]
    T5[Evolution]
    C5[Generate proposals for deviations over threshold]
    P1[Throughput deviation to fast lane]
    P2[Accuracy deviation to quality work]
    P3[Stability deviation to incident board]
    P4[Cost deviation to org wide]
    P5[Evolution deviation to strategy]
    C6[Write JSONL log]
    C7[Push urgent proposals to board]

    C1 --> C2 --> C3 --> C4 --> C5 --> C6 --> C7
    C4 --> T1
    C4 --> T2
    C4 --> T3
    C4 --> T4
    C4 --> T5
    C5 --> P1
    C5 --> P2
    C5 --> P3
    C5 --> P4
    C5 --> P5
```

### Spec Competition + ELO

```mermaid
graph TD
    S1[Task enters competition mode]
    S2[Policy gate, focus keywords and blocked domains]
    S3[Queue waiting for evaluation slot]
    S4[Rejected below threshold]
    S5[Agent A writes spec]
    S6[Agent B writes spec]
    S7[Reviewer scores correctness alignment risk]
    S8[Winner dispatched]
    S9[Loser archived with feedback]
    S10[Update ELO ratings]
    S11[spec elo JSON]
    S12[Winner spec sent to workers]
    S13[Codex worker and Gemini worker]
    S14[Spec callbacks]
    S15[Judge evaluates result]
    S16[Ready specs returned to board]

    S1 --> S2
    S2 --> S3
    S2 --> S4
    S3 --> S5
    S3 --> S6
    S5 --> S7
    S6 --> S7
    S7 --> S8
    S7 --> S9
    S8 --> S10 --> S11
    S9 --> S10
    S8 --> S12 --> S13 --> S14 --> S15 --> S16
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
