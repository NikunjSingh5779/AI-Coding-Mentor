# 08 — Rollback and Failure Handling

## 1. Principles

1. Every phase is reversible: work happens on a branch, ends in a tag, and each optional module has a switch.
2. Failures degrade the experience; they do not stop it. Markers and template explanations survive the loss of the LLM, runner, database or vision module.
3. The product never modifies the learner's machine. It reads the shared screen (screen mode) and writes only inside its own editor and database.
4. A failed verification is reported, not worked around: stop, show the output, and agree the next step with you.

## 2. Phase gate protocol

Before a phase: confirm the previous tag exists, the working tree is clean, and the database is backed up if migrations are involved. During: commit in small steps on `phase/<n>-<slug>`. After: run the phase verification, update the checklist, get your confirmation, tag `phase-<n>-complete`, merge.

## 3. Rollback by layer

| Layer | How to roll back |
|---|---|
| Code | Revert or reset the branch to the previous phase tag; nothing else depends on an unmerged branch |
| Database | Back up first, then `alembic downgrade` to the previous revision; if a downgrade is unsafe, restore the backup |
| Configuration | Flip the switch in section 5; no code change needed |
| Containers | Stop the services and remove volumes with `make db-down`; rebuild images with `make sandbox-build` |

Destructive schema changes follow expand-then-contract: add the new structure, move the code, then remove the old structure in a later phase, so one step back is always possible.

## 4. Per-phase rollback

| Phase | Rollback action | Data impact | Check afterwards |
|---|---|---|---|
| PH0 | Delete the branch or reset; `make db-down` | None; nothing is deployed | `make check` on the previous commit |
| PH1 | Revert the branch | None | Previous phase tests pass |
| PH2 | Revert, or set `ENABLED_ANALYZERS` to restore the placeholder | None | Smoke test S1 behaves as before |
| PH3 | `EXECUTION_ENABLED=false`, revert, stop runner containers | None | Markers work; Run reports "unavailable" |
| PH4 | `LLM_ENABLED=false` for template-only mode; revert the branch; revert a prompt version like code | Stored hints keep their `prompt_version` | Scenario S6 passes |
| PH5 | Back up, then `alembic downgrade`; revert | Rows created since the migration are lost on downgrade unless restored from backup | Migration up and down on an empty database; app starts |
| PH6 | `ADAPTATION_ENABLED=false`; hide the dashboard route; revert | None | Mentor behaves as in PH4 |
| PH7 | `FEATURE_SCREEN_SOURCE=false`; set `AUTO_CODE_DISCOVERY_ENABLED=false`; revert the isolated vision module if needed | None; no frames were ever stored | Editor source and floating mentor remain usable |
| PH8 | Remove the language from `ENABLED_LANGUAGES`; revert | Sessions in that language remain stored | Python path unchanged |
| PH9 | Return to the last phase tag; disable optional modules; downgrade database | As PH5 | Release checklist re-run |

## 5. Kill switches and feature flags

| Setting | Effect when off or changed | Phase |
|---|---|---|
| `EXECUTION_ENABLED=false` | No code runs; Run reports "unavailable"; analysis continues | PH3 |
| `LLM_ENABLED=false` | Template-only mentor; notice shown | PH4 |
| `MENTOR_PROACTIVITY_DEFAULT=off` | Mentor speaks only on request | PH4 |
| `FEATURE_SCREEN_SOURCE=false` | Screen source disabled; editor source unaffected | PH7 |
| `AUTO_CODE_DISCOVERY_ENABLED=false` | Automatic code-region discovery disabled; screen mode requires the manual fallback region before OCR/analysis | PH7 |
| `FLOATING_MENTOR_ENABLED=false` | Floating mentor disabled; normal mentor panel remains available | PH4 |
| `ENABLED_ANALYZERS` | Removes a failing analyzer from the fast path | PH2 |
| `ENABLED_LANGUAGES` | Removes a language | PH8 |
| `ADAPTATION_ENABLED=false` | Disables rule-based adaptation | PH6 |
| `STORE_CODE_TEXT=false` | Checkpoints keep hashes only | PH5 |

`session.ready` reports which features are active so the interface hides what is off.

## 6. Failure matrix

| Component | Failure | Detection | Learner sees | Automatic recovery | Manual recovery |
|---|---|---|---|---|---|
| LLM provider | Server stopped, model not loaded, wrong model identifier | Readiness check against the model list; request timeout P-11; circuit breaker | Template hint and a notice that AI explanations are unavailable | Breaker probes again; resumes when healthy | Start LM Studio and load the model; fix `LLM_MODEL`; or `LLM_ENABLED=false` |
| LLM provider | Slow response | Timeout P-11 | Template hint and a notice | Next trigger tries again | Smaller model or shorter context; revisit the bake-off |
| LLM output | Invalid or non-compliant | Guardrails | A normal hint if the retry succeeds, otherwise a template hint | One retry, then template | Review the prompt version |
| LLM budget | Exhausted in hosted mode | Budget counters | Template hints and a notice | Resets at the end of the period | Raise the budget P-15 |
| Sandbox runner | Down or busy | Health check; job rejection | "Run unavailable" or "busy, try again"; markers keep working | Circuit breaker probes again | Restart the runner; `EXECUTION_ENABLED=false` |
| Sandbox job | Timeout, out-of-memory, output flood | Runner limits | A runtime result with the right category | Container removed | None needed |
| Sandbox images | Missing or outdated | Runner start-up check | "Run unavailable" | None | `make sandbox-build` |
| Database | Down mid-session | Connection errors | Banner: progress is not being saved; the session continues | Bounded in-memory retry queue, flushed when back | Restart the database; restore a backup if needed |
| Migration | Fails | Alembic error (PostgreSQL runs schema changes in transactions) | Nothing; this happens at deploy time | Transaction rolls back | `alembic downgrade` or restore the backup |
| WebSocket | Connection drops | Heartbeat and close event | "Reconnecting" banner | Backoff with jitter, then `session.resume` and resend of the latest snapshot | Reload the page |
| Analyzer | Timeout, crash, tool not installed | Worker timeout P-07; exit status | Markers from the other analyzers and a notice naming the missing one | The failed analyzer is skipped for that snapshot | Fix the installation; adjust `ENABLED_ANALYZERS` |
| Vision | Low confidence, worker crash, or automatic code region not acquired | Confidence gate P-14/P-16; worker error | `source.notice`, no diagnostics | Worker restarts; sampling/reacquisition continues | Switch to the editor source; use manual region; or `FEATURE_SCREEN_SOURCE=false` |
| Screen capture | Permission revoked or the shared window closed | The stream's track ends | "Capture stopped" banner | None | Share again |
| Contracts | Frontend and backend types out of sync | CI diff check; runtime validation error | An `error` message | None | `make types` |

### Screen-specific failure rules

- **No region acquired:** emit `source.notice`; do not send code diagnostics or mentor hints.
- **Wrong or ambiguous candidate regions:** keep the previous stable region only while confidence remains valid; otherwise pause and request manual selection.
- **Region lost after window movement:** attempt reacquisition; stale diagnostics and overlay positions are dropped until a new region is valid.
- **Floating mentor obstructs code:** reposition using P-17; if no safe position exists, dock the mentor in the in-page UI instead of covering the active code.

## 7. Backup and restore (PostgreSQL in Docker)

```bash
docker compose exec db pg_dump -U <user> <database> > backup.sql
docker compose exec -T db psql -U <user> <database> < backup.sql
```

Take a backup before every migration that touches existing data. Test a restore at least once before PH9.

## 8. When a phase fails verification

1. Stop. Do not mark the phase done.
2. Report the failing command and its real output.
3. Say which requirement or exit criterion is affected and whether the cause is understood.
4. Offer options (fix forward, roll back, change the plan) and wait for your decision.
5. If the plan changes, record an ADR and update the affected planning files.

## 9. Incident basics

- Stop code execution at once with `EXECUTION_ENABLED=false`.
- Purge stored code with the delete-my-data function or by setting `STORE_CODE_TEXT=false` and running the retention purge.
- Rotate `SANDBOX_SECRET` and any LLM key if exposure is suspected.
- Reproduce with fixtures; logs never contain code, so a bug report needs a snippet from the person affected.
