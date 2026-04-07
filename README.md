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

The diagrams below show each layer of the pattern. PNG versions render everywhere. Mermaid source files are in `diagrams/*.mmd` for use in Obsidian or other Mermaid-compatible tools.

### Full Architecture
![ARCHITECTURE](diagrams/ARCHITECTURE.png)

### Layer 1 - Board
![BOARD](diagrams/BOARD_LAYER.png)

### Layer 2 - Lane Workers
![LANE](diagrams/LANE_WORKERS.png)

### Layer 2 - Orchestration API
![API](diagrams/MC_API.png)

### Layer 2 - Cron Scheduler
![CRON](diagrams/CRON_ORCHESTRATOR.png)

### Layer 2 - Spec Competition + ELO
![SPEC](diagrams/SPEC_COMPETITION.png)

---

## What's Included

| Path | Description |
|------|-------------|
| `docs/ARCHITECTURE.md` | Full architecture doc |
| `docs/SLA.md` | Lane-aware SLA/escalation matrix |
| `diagrams/*.mmd` | Mermaid source files |
| `diagrams/*.png` | Pre-rendered diagrams |
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
