# Nik_kiT — Tests (phase gates)

> **Rule:** before a feature phase (P1, P2, …) is concluded, **all its applicable
> tests must pass.** Only tests possible in the current environment are in scope —
> right now that's **localhost** (Docker stack up); prod-only checks are deferred.

## Naming convention

Every test has an id: **`TEST_P<phase>_T<NN>`** — e.g. `TEST_P0_T01`, `TEST_P1_T03`.
- `P<phase>` = the phase it guards (`P0`, `P1`, …).
- `T<NN>` = a two-digit sequence within that phase.

Tests live in `test_p<phase>.py` and register via the `@test("TEST_P1_T0X", "...")`
decorator from [`lib.py`](lib.py).

## What kind of tests these are (for now)

**Lightweight, stdlib-only integration/smoke tests** that hit the **live localhost
stack** over HTTP (no pip installs, no test database, no prod). They assert the
phase's gate behaviour end-to-end (API → DB). Heavier unit tests / frontend e2e can
be layered in later without changing the runner or the naming.

## How to run

```bash
# 0) stack must be up (and seeded for P1)
cd infra && docker compose up -d
docker compose exec -T app python manage.py seed_menu

# 1) run tests (from repo root)
python3 tests/run_tests.py          # all phases
python3 tests/run_tests.py P1       # just P1
python3 tests/run_tests.py P0 P1    # multiple
```

Exit code is `0` when everything passes, `1` otherwise — so it doubles as a
pre-push / phase-completion gate. Override targets with env vars if needed:
`NIKKIT_API` (default `http://localhost:6061`), `NIKKIT_UI` (default `http://localhost:8080`).

## Current coverage

| Phase | Tests |
|---|---|
| **P0** | `TEST_P0_T01` health ok + db connected · `TEST_P0_T02` web serves + proxies API |
| **P1** | `TEST_P1_T01` sections in order · `T02` UNAVAILABLE shown/HIDDEN excluded · `T03` savoury customization embedded · `T04` sweets have none · `T05` store status open · `T06` unknown recipe 404 · `T07` admin reachable · `T08` included default accompaniments (pickle/chutney) · `T09` Raita (+40) add-on |
| **P2** | `TEST_P2_T01` register idempotent by phone · `T02` server-side price · `T03` required option 400 · `T04` unavailable 409 · `T05` checkout needs token · `T06` order→PLACED + cart closed · `T07` own-orders-only |
| **P3** | `TEST_P3_T01` payment info (UPI+amount+QR) · `T02` PLACED stage · `T03` proof→PAYMENT_SUBMITTED · `T04` proof needs image · `T05` admin login · `T06` confirm→ACCEPTED (one notice) · `T07` advance lifecycle + illegal 409 · `T08` confirm admin-only · `T09` reject→re-upload · `T10` notifications logged+idempotent |
| **P4** | *(M09 closures)* `TEST_P4_T01` open by default · `T02` closure→closed + message + reopens_on · `T03` checkout 409 STORE_CLOSED while browsing/cart work · `T04` delete closure reopens · `T05` closures admin-only · `T06` future closure ≠ today · `T07` bad date range 400 · *(M10 ratings)* `T08` can't rate non-completed 409 · `T09` rate completed 201 + read back · `T10` stars 1–5 & note ≤100 validation · `T11` one per order (409) + PATCH · `T12` admin summary/list · `T13` own-only + admin-token |
| **P5** | *(M12 chef & social)* `TEST_P5_T01` About-Chef profile + Instagram bstvaranasi · `T02` recipe with chef-style link exposes it · `T03` recipe without → `chef_style: null` · `T04` chef edit gated (admin login) |
| **P6** | *(order modes)* `TEST_P6_T01` Order now → ready_by set · `T02` Order for later → scheduled_for · `T03` later needs time 400 · `T04` too-soon 400 · `T05` closed date 409 STORE_CLOSED · `T06` ordering-disabled recipe not orderable · `T07` default = ORDER_NOW |
| **P7** | *(M13 account + M01 OTP)* `TEST_P7_T01` PATCH /auth/me (phone stays identity) · `T02` bad email 400 · `T03` OTP request existing 200/unknown 404 · `T04` OTP verify restores same account / wrong code 400 · `T05` restored token sees own order history · `T06` /auth/me needs token |

Add a phase's tests as you build it; keep this table and the runner in sync.
