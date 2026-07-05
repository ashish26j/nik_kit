# Nik_kiT — Git Workflow (branch-per-phase)

> **Audience:** everyone (AI + human). **Status:** ACTIVE convention — follow every time.
> This is the agreed way we checkpoint work. Read before committing/pushing.

---

## 1. Remote

- **Repo:** `https://github.com/ashish26j/nik_kit.git`
- **Default branch:** `main` (PRs/merges to `main` happen **later** — not now).
- **Auth:** a GitHub PAT lives under key `GITHUB_PAT_TOKEN` in **`infra/.env`**
  (git-ignored — **never** in `infra/env/.env.example` or any tracked file).

## 2. The rule: one branch per phase, cumulative

Each phase (P0, P1, P2, …) gets its own branch. Every new phase branches **from the
previous phase's branch**, so each branch carries **all prior phases' work + its own**.

```
main
 └── P0_INFRA          ← all P0 work, pushed when P0 is done
      └── P1_APP_MENU   ← branched FROM P0_INFRA → contains P0 + P1
           └── P2_...    ← branched FROM P1_APP_MENU → contains P0 + P1 + P2
                └── …
```

**Branch naming:** `P<n>_<SHORT_CAPS_LABEL>` — e.g. `P0_INFRA`, `P1_APP_MENU`,
`P2_CART_ORDER`, `P3_PAYMENT`, `P4_ADMIN`, `P5_WEB`, `P6_RELEASE`.

## 3. Per-phase procedure

**While working a phase:** stay on that phase's branch and commit changes to it as you go.

**When a phase is done:**
1. Commit all remaining changes to the phase branch.
2. **Push** the phase branch to `origin`.
3. Create the **next** phase's branch **from the current one** and continue there.

> PRs and merging into `main` are deferred — for now we only **capture each phase's
> work on its branch and push it**. Do not open PRs or merge unless explicitly asked.

## 4. Commands (reference)

```bash
# One-time setup
cd nik_kit
git init
git remote add origin https://github.com/ashish26j/nik_kit.git

# --- finishing a phase (example: P0) ---
git checkout -b P0_INFRA          # (first phase; later phases branch from prev)
git add -A
git status                        # sanity check what's staged
git ls-files | xargs grep -l 'github_pat' && echo "STOP: token tracked!" || echo "no token tracked"
git commit -m "P0: infrastructure — 3 containers + Django health + Expo boot"

# push using the PAT from infra/.env WITHOUT storing it in .git/config
TOKEN=$(grep '^GITHUB_PAT_TOKEN=' infra/.env | cut -d= -f2-)
git push "https://x-access-token:${TOKEN}@github.com/ashish26j/nik_kit.git" P0_INFRA

# --- starting the next phase (P1) from P0 ---
git checkout -b P1_APP_MENU       # from P0_INFRA → carries P0 + P1
# …do P1 work, commit to P1_APP_MENU, push when P1 is done…
```

## 5. Security rules (non-negotiable)

- **Never commit the PAT** or any secret. It lives only in `infra/.env` (git-ignored).
- The token is **not** stored in `.git/config`; it's passed inline on `push` only.
- Before every push, run the `git ls-files | xargs grep github_pat` guard above.
- If a secret is ever committed, **stop**, rotate the token, and scrub history before pushing.

## 6. What's tracked vs ignored

- **Ignored** (see [`.gitignore`](../.gitignore)): `infra/.env`, `node_modules/`,
  `frontend/.expo/`, `__pycache__/`, media, build artifacts.
- **Tracked:** source (`backend/`, `frontend/` sans deps, `infra/` configs), `docs/`,
  `progress/tracker.json`, `infra/env/.env.example` (template, **placeholder secrets only**).
