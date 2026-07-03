# PMO Toolkit — Enhancement Pack (v-next)

All changes are additive and backward compatible. Default behaviour with no
new configuration is identical to the current deployed app.
Test suite: 8/8 passing (was 6/7 — one stale test fixed, one new test added).

## Files changed / added
| File | Change |
|---|---|
| `app.py` | New nav entry (Portfolio Weekly Digest), optional role PIN gate, seed/reset restricted to Admin when PINs configured |
| `config.py` | New optional `PM_ROLE_PINS` setting + parser; digest added to Sponsor/Customer visibility |
| `core/ai.py` | New `portfolio_summary()` — AI narrative with deterministic offline fallback (appended, nothing modified) |
| `modules/portfolio_digest.py` | **NEW** — Portfolio Weekly Digest page (read-only, cannot affect other modules) |
| `tests/test_models.py` | Fixed stale `Royal FRS` assertion → `Meridian Group`; added digest regression test |

## 1. Portfolio Weekly Digest (new module)
The "Monday morning" delivery-head view: portfolio KPIs, AI/offline narrative,
per-project SPI/CPI/health table, top open risks across all projects, slipped
milestones, and a copy-ready email digest with .txt download. This is the demo
centrepiece for the AI-Enabled PMO offer.

## 2. Role PIN protection (optional, off by default)
Streamlit Cloud secret:
    PM_ROLE_PINS = "Admin:2468,PM:1357"
- Unset (default): app behaves exactly as today.
- Set: selecting a protected role prompts for a PIN in the sidebar; wrong PIN
  falls back to Customer. Seed/reset (which wipes ALL data) becomes Admin-only.
This closes the hole where any visitor to the public URL could reset the DB.

## 3. Test suite repair
`test_seed_and_relationships` asserted the old `Royal FRS` customer name and
has been failing since the Meridian rename. Fixed; CI is green again.

## Deploy
Drop the five files into the repo at the same paths, commit, push.
Streamlit Cloud redeploys automatically. No schema changes, no migration.

## Recommended next (not included — needs your call)
1. **Weekly EVM snapshots** — new `PortfolioSnapshot` table written on demand,
   enabling SPI/CPI trend lines over time (create_all adds the table safely).
2. **Audit log** — record who changed what in the MACD grids (needs identity,
   so best after PIN/auth is in use).
3. **SQLAlchemy 2.0 cleanup** — `Query.get()` in `modules/common.py` is
   legacy-deprecated; migrate to `Session.get()` when convenient (works today).

---

# v-next.2 — EVM Trend History (additive)

Test suite: 9/9 passing.

| File | Change |
|---|---|
| `core/models.py` | **NEW model** `PortfolioSnapshot` (appended; create_all adds the table to existing SQLite/Postgres DBs automatically — no migration) |
| `core/snapshots.py` | **NEW** — idempotent snapshot capture (auto once/day + on-demand upsert) and history query |
| `modules/portfolio_digest.py` | New "Trends over time" section: portfolio avg SPI/CPI line chart + per-project metric selector, themed via `style_fig` |
| `tests/test_models.py` | New regression test: capture is idempotent, ensure_daily short-circuits, history spans dates |

Behaviour: opening the Portfolio Weekly Digest captures at most one snapshot
per calendar day; the "Capture snapshot now" button refreshes today's rows
(upsert — safe to click repeatedly). Trend charts appear from the second day
of history. For demos, call `capture_snapshot(date - N days)` from a Python
shell to backfill a few weeks instantly.
