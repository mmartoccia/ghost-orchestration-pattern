# Three-Layer Task Orchestration Pattern

A production-proven architecture for running multi-agent task execution with human oversight.

**Core principle:** Humans define what matters. Machines decide what moves next.

---

## The Problem

Most automation fails at the human/machine boundary:
- Machines execute but humans don't know what's happening
- Humans介入 too often, creating bottlenecks
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
# 1. Define your lanes in board.yaml
lanes:
  - name: product
    priority: fast
    escalation_minutes: 60
  - name: data
    priority: medium
    escalation_minutes: 240

# 2. Start the daemon
python3 examples/minimal_daemon.py

# 3. Watch the log
tail -f orchestration.log.jsonl
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: BOARD                                            │
│  Topic lanes → Incident board → Human triage + escalation    │
└──────────────────────┬──────────────────────────────────────┘
                       │ task dispatch
┌──────────────────────▼──────────────────────────────────────┐
│  LAYER 2: ORCHESTRATION                                    │
│  Task Loop (daemon)  ─  Cron Scheduler  ─  Lane Workers     │
│  Optional: Spec Competition (multi-agent decision mode)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ read / write
┌──────────────────────▼──────────────────────────────────────┐
│  LAYER 3: DATA                                             │
│  Canonical source → ETL/sync → Derived store                │
└─────────────────────────────────────────────────────────────┘
```

Full documentation: see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## What's Included

| Path | Description |
|------|-------------|
| `docs/ARCHITECTURE.md` | Full architecture doc (pattern only, no implementation) |
| `docs/SLA.md` | Lane-aware SLA/escalation matrix |
| `diagrams/` | Mermaid diagrams for each layer |
| `examples/minimal_daemon.py` | Minimal working reference implementation |
| `examples/task_schema.yaml` | YAML task schema with all recommended fields |
| `examples/schema.json` | JSONL orchestration log schema |

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

The `reference/` directory contains production-tested implementation patterns extracted from a live system:

| File | Description |
|------|-------------|
| `reference/BOARD_LAYER.md` | Coordination boards, topic lanes, incident routing, task block schema |
| `reference/LANE_WORKERS.md` | Per-lane background processor pattern, startup supervisor, health checks |
| `reference/MC_API.md` | 5-endpoint REST API for task coordination, atomicity contract, Flask implementation |
| `reference/CRON_ORCHESTRATOR.md` | 15-min scheduler, TASTE rubric, metrics to collect, alert routing |
| `reference/SPEC_COMPETITION.md` | Multi-agent decision mode, ELO rating system, reviewer scoring rubric |

These are **reference patterns**, not drop-in implementations. They show how each layer works in production. Adapt to your stack.

## Status

Pattern is production-proven. Reference implementations are skeletons — adapt to your stack.

MIT License.
