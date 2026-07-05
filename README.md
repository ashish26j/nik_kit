# Nik_kiT

A lightweight, foody food-ordering app — **Parathas · Snacks · Sweets**. Explore
freely, customize a dish, check out in seconds, pay by UPI. One codebase (Expo) runs
on **web + Android**; a **Django + MySQL** backend serves the data.

> **Status:** **P0 — infrastructure**. Proving the pipeline: 3 containers + the Expo
> app booting on a phone and reaching the backend. Features arrive in P1+.

## Docs (read these first)
- [`docs/blueprint.md`](docs/blueprint.md) — the one-page product vision + roles.
- [`docs/02-architecture.md`](docs/02-architecture.md) — stack, containers, topology.
- [`docs/01-toolchain-explained.md`](docs/01-toolchain-explained.md) — Expo/Metro/Django, plainly.
- [`docs/contracts/`](docs/contracts/) — the 10 module contracts (behavior before code).
- [`docs/03-git-workflow.md`](docs/03-git-workflow.md) — **branch-per-phase git workflow** (follow every time).
- [`progress/tracker.json`](progress/tracker.json) — phase/step tracker (source of truth).

## Layout
```
backend/   Django + DRF API (the "brain")           → app container, port 6061
frontend/  Expo (React Native + Web)                → phone via Expo Go; web via ui container
infra/     docker-compose + Dockerfiles + env       → db · app · ui
progress/  tracker.json                             → phases & steps
docs/      blueprint · architecture · contracts
```

## Run it locally (P0)

**Prerequisites:** Docker Desktop running · Node 20+ · the **Expo Go** app on your
phone · phone and laptop on the **same Wi-Fi**.

### 1. Backend + web (Docker)
```bash
cp infra/env/.env.example infra/.env      # first time only
cd infra
docker compose up --build                 # starts db, app (6061), ui (8080)
```
Verify:
```bash
curl http://localhost:6061/api/v1/health          # {"status":"ok","db":"connected"}
open http://localhost:8080                          # web placeholder shows "backend: ok ✅"
```

### 2. App on your phone (Metro on host — NOT a container)
```bash
cd frontend
npm install
npx expo start --port 6060                # scan the QR with Expo Go
```
The app calls the backend at your **laptop's LAN IP** on port **6061**
(e.g. `http://192.168.1.13:6061`). Set/confirm it in
[`frontend/config/api.js`](frontend/config/api.js).

## Ports
| Service | Port | Purpose |
|---|---|---|
| Metro (host) | 6060 | serves app **code** to Expo Go (dev only) |
| Django `app` | 6061 | serves app **data** (REST API) |
| Web `ui` | 8080 | browser experience (P0 placeholder) |
| MySQL `db` | 3306 | database (localhost-published for dev) |
