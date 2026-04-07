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
flowchart TB
    subgraph B["LAYER 1 - BOARD"]
        L1["Human work intake + Triage"]
        LANES["fast-lane / medium-lane / slow-lane"]
        INC["incident-board.md (cross-lane)"]
        L1 --> LANES
        LANES --> INC
    end
    B --> O
    subgraph O["LAYER 2 - ORCHESTRATION"]
        L["Task Loop Daemon (WIP=1)"]
        C["Cron Scheduler (15min TASTE)"]
        S["Spec Competition (ELO)"]
        W["Lane Workers"]
    end
    O --> D
    subgraph D["LAYER 3 - DATA"]
        P["Canonical Source (append-only)"]
        Y["ETL Sync (schema validation)"]
        R["Derived Store (PostgreSQL / SQLite)"]
        P --> Y --> R
    end
    L -.-> LOG["orchestration.log.jsonl"]
    C -.-> LOG
```

---

### Board Layer

```mermaid
flowchart TD
    A["Inbound Signals - Telegram / Email / Cron / Alert"] --> B["Human Triage - choose lane and priority"]
    B --> C["fast-lane.md - Product / API"]
    B --> D["medium-lane.md - Data / ETL"]
    B --> E["slow-lane.md - Strategy"]
    B --> F["incident-board.md - cross-lane"]
    C --> C1["Telegram Topic 6"]
    D --> D1["Telegram Topic 5"]
    E --> E1["Telegram Topic 3"]
    F --> F1["Telegram Topic 1"]
```

### Lane Workers

```mermaid
flowchart TD
    L["lane.md - task blocks"] --> P
    P --> L
    P["poll_lane() - check for ready tasks"] --> R["Sort by priority - pick next task"]
    R --> E["execute task - do the work"]
    E --> W["write_result() - update Board"]
    W --> P
    W --> T1["Fast Worker - 30-60s cycle"]
    W --> T2["Medium Worker - 2-5 min cycle"]
    W --> T3["Slow Worker - 5-15 min cycle"]
    W -.-> H["worker.json - Heartbeat"]
    H -.-> S["Supervisor - auto-restart"]
```

### Orchestration API

```mermaid
flowchart TD
    C1["Daemon"] --> A
    C2["Worker"] --> A
    C3["Human"] --> A
    C4["Cron"] --> A
    subgraph A["ORCHESTRATION API /api"]
        G1["GET /tasks"]
        G2["GET /tasks/id/blockers"]
        G3["GET /tasks/id/dependents"]
        P["POST /tasks/id/status"]
        G4["GET /handoffs"]
    end
    P --> S
    subgraph S["POST atomicity sequence"]
        X1["1. Write log FIRST"]
        X2["2. Update task state"]
        X3["3. Check handoff protocol"]
        X4["4. Send notification"]
        X1 --> X2 --> X3 --> X4
    end
```

### Cron Scheduler

```mermaid
flowchart TD
    E["Every 15 minutes"] --> M1
    subgraph C["RUN CYCLE"]
        M1["1. Collect Metrics"] --> M2["2. Analyze Outputs"]
        M2 --> M3["3. Evaluate TASTE Rubric"]
        M3 --> M4["4. Generate Proposals"]
        M4 --> M5["5. Write JSONL Log"]
        M5 --> M6["6. Push to Board"]
    end
    M3 -.-> T
    subgraph T["TASTE RUBRIC"]
        T1["Throughput"]
        T2["Accuracy"]
        T3["Stability"]
        T4["Cost"]
        T5["Evolution"]
    end
    M4 --> P1["Throughput - Fast-lane"]
    M4 --> P2["Accuracy - Quality"]
    M4 --> P3["Stability - Incident"]
    M4 --> P4["Cost - Org-wide"]
```

### Spec Competition + ELO

```mermaid
flowchart TD
    T["Task enters competition"] --> P["Policy gate - focus and block thresholds"]
    P -->|"pass"| Q["task-queue - wait for slot"]
    P -->|"fail"| RJ["rejected"]
    Q --> A["Agent A writes spec"]
    Q --> B["Agent B writes spec"]
    A --> V["Reviewer scores both - quality x alignment x risk"]
    B --> V
    V --> W["Winner dispatched"]
    V --> L["Loser archived"]
    W -.->|"ELO up"| E1["Agent A rating increases"]
    L -.->|"ELO down"| E2["Agent B rating decreases"]
    E1 --> EL["spec-elo.json"]
    E2 --> EL
    W --> WK["Workers execute spec"]
    WK --> CB["spec-callbacks"]
    CB --> J["Judge evaluates result"]
```

---

## What's Included

| Path | Description |
|------|-------------|
| `docs/ARCHITECTURE.md` | Full architecture doc |
| `docs/SLA.md` | Lane-aware SLA/escalation matrix |
| `diagrams/*.mmd.source` | Mermaid source files (for Obsidian / local tools) |
| `diagrams/*.png` | Pre-rendered fallback PNGs |
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
