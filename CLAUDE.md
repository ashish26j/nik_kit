# Nik_kiT — project conventions (read first)

Lightweight food-ordering app — Parathas · Snacks · Sweets. Expo (RN + Web) frontend,
Django + DRF backend, MySQL, 3 Docker containers (ui/app/db).

## Start here
- **Vision & roles:** [`docs/blueprint.md`](docs/blueprint.md)
- **Architecture & containers:** [`docs/02-architecture.md`](docs/02-architecture.md)
- **Module contracts (behavior before code):** [`docs/contracts/`](docs/contracts/) — M01…M10
- **Phase/step tracker (source of truth):** [`progress/tracker.json`](progress/tracker.json)

## Working rules (do these every time)
1. **Contracts before code.** Behavior is agreed in `docs/contracts/` first; code must match.
2. **Git = branch per phase (cumulative).** Full rule: [`docs/03-git-workflow.md`](docs/03-git-workflow.md).
   Branches: `P0_INFRA`, then `P1_APP_MENU` **from** `P0_INFRA`, etc. Each phase branch
   carries all prior phases. Push each phase branch when the phase is done; **no PRs/merges
   to `main` unless explicitly asked.**
3. **Never commit secrets.** The GitHub PAT (`GITHUB_PAT_TOKEN`) lives only in the
   git-ignored `infra/.env`. Run `git ls-files | xargs grep github_pat` before any push.
4. **No network/firewall changes** (policy). Verify the app on the **laptop over loopback**
   (Expo **web**: `cd frontend && npx expo start --web --port 6060` → calls backend at
   `localhost:6061`). Phone/LAN testing is deferred until a firewall-free network exists.
5. **Tests are the phase gate.** Before concluding any feature phase, **all its
   applicable tests must pass**: `python3 tests/run_tests.py P<n>`. Tests are
   lightweight, stdlib-only, hit the live localhost stack, and are numbered
   `TEST_P<phase>_T<NN>`. Add each phase's tests as you build it. See [`tests/`](tests/).
6. **Ports:** Metro 6060 · Django 6061 · web/ui 8080 · MySQL 3306 (internal).

## Run locally
```bash
cd infra && docker compose up -d          # db + app(6061) + ui(8080)
cd frontend && npx expo start --web --port 6060   # the app, in the browser (loopback)
```
