# Lane-Aware SLA Escalation

**Problem:** A flat "escalate after 48 hours" rule treats a stale data pipeline the same as a stale strategy document. They're not equivalent.

**Solution:** Define urgency by lane. Fast lanes escalate fast. Slow lanes tolerate longer.

---

## Default Lane Definitions

| Lane | Characteristics | Examples |
|------|----------------|---------|
| **Fast** | Customer-facing, revenue-critical | Product surfaces, API, user-facing features |
| **Medium** | Internal tooling, ops | Data pipelines, ETL, internal dashboards |
| **Slow** | Knowledge work, planning | Strategy, research, positioning |

---

## SLA Matrix

### Fast Lane (e.g., Product, API)

| Severity | Claim window | Motion window |
|----------|-------------|---------------|
| Critical | Immediate | Immediate |
| High | 15 minutes | 60 minutes |
| Medium | 60 minutes | 4 hours |
| Low | 8 hours | 24 hours |

**Rule:** If a live or demo-critical product surface is degraded, escalate immediately. No passive waiting.

### Medium Lane (e.g., Data, Pipeline, Engineering)

| Severity | Claim window | Motion window |
|----------|-------------|---------------|
| Critical | 30 minutes | Immediate |
| High | 2 hours | 90 minutes |
| Medium | 6 hours | 12 hours |
| Low | 24 hours | 48 hours |

**Rule:** Freshness incidents escalate faster. If stale data is already feeding a live surface, promote severity one level.

### Slow Lane (e.g., Strategy, Research)

| Severity | Claim window | Motion window |
|----------|-------------|---------------|
| Critical | 4 hours | Immediate |
| High | 24 hours | 48 hours |
| Medium | 3 days | 5 days |
| Low | 7 days | 10 days |

**Rule:** Strategy work escalates when a decision is blocking delivery — not merely because a document is old.

---

## Default Severity Map

When seeding tasks, infer severity from the visible impact:

| Situation | Default Severity |
|-----------|-----------------|
| Customer-visible outage | Critical |
| Broken core surface | Critical |
| Corrupted/stale data on active surface | Critical |
| Major degradation | High |
| Blocked execution on priority path | High |
| Real defect, contained blast radius | Medium |
| Polish, non-urgent optimization | Low |
| Slow narrative work | Low |

---

## Motion Signal

"Visible motion" means one of:
- Task status explicitly updated
- Blocker state changed
- Worker heartbeat/lease refreshed with matching board update
- Incident status moved forward

**Silent ownership does not count.** If a task is `in-progress` but nothing on the board has changed, the motion window is still ticking.

---

## Escalation Triggers

A task should escalate when any of these are true:

1. Claim window exceeded (task unclaimed after N minutes/hours)
2. Motion window exceeded (no visible progress after N minutes/hours)
3. Same task stale-reopens twice in 24 hours
4. Task bounces across lanes without a stable owner
5. Blocker is holding a higher-priority lane hostage
6. Severity promoted because downstream surface is now affected

---

## Severity Promotion Rules

Promote severity one level when:
- Stale data is already consumed by a live surface
- A defect affects a live customer or demo
- Strategy delay blocks active delivery in a faster lane
- A delay blocks an active launch or outbound campaign

Do not promote above `Critical`.

---

## Per-Lane Configuration (YAML)

```yaml
lanes:
  - name: fast
    claim_minutes: 15
    motion_minutes: 60
    escalations:
      critical: immediate
      high: { claim: 15, motion: 60 }
      medium: { claim: 60, motion: 240 }
      low: { claim: 480, motion: 1440 }

  - name: medium
    claim_minutes: 120
    motion_minutes: 90
    escalations:
      critical: { claim: 30, motion: immediate }
      high: { claim: 120, motion: 90 }
      medium: { claim: 360, motion: 720 }
      low: { claim: 1440, motion: 2880 }

  - name: slow
    claim_minutes: 1440
    motion_minutes: 2880
    escalations:
      critical: { claim: 240, motion: immediate }
      high: { claim: 1440, motion: 2880 }
      medium: { claim: 4320, motion: 7200 }
      low: { claim: 10080, motion: 14400 }
```
