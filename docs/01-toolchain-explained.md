# Nik_kiT — Toolchain Explained (Expo · Metro · Expo Go · Backend)

> **Audience:** the whole team, including anyone new to mobile development.
> **Goal:** understand *in very simple terms* how our code becomes a running app,
> and why it works the way it does. Read this once and the rest of the project
> will make sense.

---

## 1. The big picture in one sentence

> We write **one** codebase. A tool called **Expo** turns it into an **Android app**,
> an **iOS app** (later), and a **website** — all at once. During development, a
> helper called **Metro** compiles our code live, and an app called **Expo Go** runs
> it on our phone instantly. The app then talks to our **Django backend** for its data.

That's the whole thing. The rest of this doc just explains each word.

---

## 2. The four players (plain definitions)

### 🧰 Expo — *the kit we build with*
A toolkit built on top of **React Native** (React Native is what lets JavaScript
become a real phone app). Expo adds all the convenience: a command-line tool,
prebuilt phone features (camera, notifications), the **Expo Go** test app, and a
cloud build service (**EAS**).

- **Role:** the overall system that turns **one codebase → Android + iOS + Web**.
- **Think of it as:** the franchise system that lets you open the same restaurant
  in many locations.

### ⚙️ Metro — *the live engine that compiles our code*
The **JavaScript bundler + dev server** that ships inside Expo. Our code is many
files; Metro packs them into one runnable bundle, serves it over the network, and
**re-bundles instantly every time we save** ("hot reload").

- **Role:** the development-time engine that **bundles + serves** our code.
- **It does NOT run the app** — it serves the code; the phone runs it.
- **Think of it as:** the kitchen line that cooks your latest recipe fresh every
  time you tweak it, and plates it out.

### 📱 Expo Go — *the app on our phone that runs the code (in dev)*
A **free app** from the Play Store. We run Metro on the laptop, it prints a QR code,
we scan it, and our app opens inside Expo Go — live-reloading as we edit.

- **Role:** the **development preview** that runs/executes our app on a real phone.
- **Important:** end users **never** use Expo Go. It's only *our* sandbox while
  building. End users get the real app from the Play Store.
- **Think of it as:** the table where the dish is served and tasted while testing.

### 🧠 Backend (Django + MySQL) — *the brain and the data*
A **separate codebase** written in Python (Django) plus a MySQL database. It holds
the menu, recipes, orders, users, and the payment-cycle logic. It has no "look" —
it just answers data requests.

- **Role:** serves the app's **data** over a REST API.
- **Think of it as:** the storeroom + head chef deciding what's available and
  recording every order.

---

## 3. How they fit together (the mental model)

We built this understanding step by step. Here is the final, correct picture.

### Three stages of turning code into a running app

```
   Code Build            →   Code Compile        →   Code Deploy & Run
   (React Native + Expo)     (METRO bundles it)      (Expo Go runs it)
      you write in Cursor      packages + serves       executes on the phone
```

### The full dev-time diagram

```
   CURSOR  (one repo: nik_kit/, TWO codebases)
   ├── frontend/  React Native + Expo ──► METRO ─────────┐  (serves CODE)
   └── backend/   Django (Python)     ──► DOCKER app+db ─┐│  (serves DATA)
                                                         ││
                                          ┌──────────────┘│
                                          │  ┌────────────┘
                                          ▼  ▼
                                   EXPO GO (phone)  /  BROWSER
                                   the running app talks to BOTH:
                                     • Metro  → to get its CODE
                                     • backend → to get its DATA
```

---

## 4. The two connections (this trips everyone up — read carefully)

The running app opens **two** separate connections. Both are the **phone reaching
OUT** to the laptop — the laptop never reaches *into* the phone.

| Connection | Purpose | When | Lifespan |
|---|---|---|---|
| **App → Metro** | get the **code** bundle | dev only | **temporary** — gone in production |
| **App → Django backend** | get/send the **data** (menu, orders, payment proof) | dev + prod | **permanent** — the real client-server link |

### Why the "two calls" is confusing — and why your classic model still holds

Your familiar model is 100% intact:

```
   UI (client)  →  Backend API  →  DB      ← this is the REAL app, always
```

The **Metro** connection is just **extra scaffolding that exists only while
developing** — a fast way to get the code onto the phone without rebuilding the app
every time. It is NOT part of the app's real functionality.

**Proof:** in production there is **no Metro at all** — the code is baked inside the
installed app:

```
DEVELOPMENT (now)                          PRODUCTION (Play Store app)
┌───────────────┐                          ┌───────────────┐
│  Expo Go       │                          │ installed app  │
│   ├─► Metro    │ (code, temporary)        │  (code baked   │  ← no Metro at all
│   └─► Backend  │ (data)                   │   inside)      │
└───────────────┘                          │   └─► Backend   │ (data)
                                           └───────────────┘
        UI → Metro + Backend                     UI → Backend  ← the classic model
```

So: **in dev, Expo Go is a pure UI client** that happens to pull its code from Metro.
In production, Metro disappears and you're left with exactly `UI client → API → DB`.

---

## 5. How the phone actually reaches the backend ("direct entry?")

The backend never enters the phone. **The app calls the backend's URL over Wi-Fi**,
exactly like a browser calling a website:

```
   PHONE (app in Expo Go)                              LAPTOP
   ┌───────────────────────────┐                ┌──────────────────────────┐
   │ app calls:                 │                │  Docker publishes port    │
   │ GET http://192.168.1.5:6061│ ── request ──► │  6061 → app (Django)      │
   │      /api/menu             │                │        │                  │
   │                            │ ◄── response ──│        ▼                  │
   │ (renders Parathas, prices) │   (JSON data)  │      db (MySQL)           │
   └───────────────────────────┘                └──────────────────────────┘
              └──────────── same Wi-Fi network ────────────┘
```

Three things must line up for this to work:

1. **Same Wi-Fi** → the phone can see the laptop at its **LAN IP** (e.g. `192.168.1.5`).
2. **Docker port publishing** → the `app` container maps Django's port to the laptop
   (`6061 host → 6061 container`).
3. **The app knows the address** → the frontend has an API base URL pointing at that
   LAN IP.

> ⚠️ **The #1 "why won't it connect" trap:** phone and laptop must be on the **same
> Wi-Fi**, and the app must use the laptop's **LAN IP** (not `localhost`, because on a
> phone `localhost` means the phone itself).

---

## 6. Development vs Production (same shape, different tools)

The pipeline has the same two-part shape in dev and prod — only the tools swap.

| Stage | **Development** (now) | **Production** (later) |
|---|---|---|
| **Build** | React Native + Expo code | *same code* |
| **Compile** | **Metro** (live, on your Mac) | **EAS** (Expo's cloud builder) |
| **Deploy & Run** | **Expo Go** on your phone | **Play Store app** + **website** for end users |

```
DEV loop:     write ─► Metro ─► Expo Go        (local build-&-run machinery)
DEV run:      Expo Go  ──►  Backend (app+db)    (the app you actually test)

PROD release: code  ─► EAS cloud build ─► Play Store   (the real CI/CD)
PROD run:     installed app ──► Backend (app+db)         (the app users run)
```

- **Metro + Expo Go** = the *local dev inner loop*.
- **EAS Build/Submit** = the real *CI/CD* — the production version of that pipeline.

---

## 7. What runs where (our Phase-1 setup)

```
   YOUR LAPTOP (M4 Pro)                          YOUR PHONE
   ┌──────────────────────────────┐              ┌───────────────┐
   │  Cursor  ── write code ──────┐│              │               │
   │  (React Native + Expo libs)  ││   same WiFi  │   Expo Go     │
   │                              ▼│  ◄─────────► │  runs the app  │
   │  METRO ── bundles + serves ──┘│              │               │
   │                               │              └───────────────┘
   │  Docker: app (Django) + db    │
   │          (MySQL) — the data   │
   └──────────────────────────────┘
```

On the laptop during development, **two things run**:
1. **Metro** (on the host) — serves the app **code** to Expo Go.
2. **Docker containers `app` + `db`** — serve the app's **data**.

Both reachable from the phone over the **same Wi-Fi**.

---

## 8. Quick FAQ

**Q: Do end users install Expo Go?**
No. Expo Go is only our dev sandbox. End users install *our* Nik_kiT app from the
Play Store (or use the website).

**Q: Is Metro heavy?**
No — it's a Node process (~0.3–1 GB RAM). Trivial on our hardware. The only heavy
optional tool is the Android Emulator, which we skip by using a real phone.

**Q: Can we run the Android Emulator or Metro in Docker?**
- **Emulator in Docker:** don't — especially on a Mac it needs hardware
  virtualization Docker can't pass through. Run it natively (or just use a real phone).
- **Metro in Docker:** possible, but on a Mac the phone/QR networking and hot-reload
  work best with Metro on the **host**. We run Metro on the host; the `ui` container
  is for the **web** build.

**Q: Why two codebases in one repo?**
The frontend (React Native + Expo) and the backend (Django/Python) are different
languages doing different jobs. They live side by side in `nik_kit/` and talk over a
REST API.

**Q: Where does the browser/web version come from?**
The *same* frontend code also compiles to a website. In production that web build is
served by the **`ui` container**.

---

## 9. One-paragraph summary (memorize this)

> We write one codebase in **Cursor** using **React Native + Expo**. **Metro** compiles
> it live and serves it; **Expo Go** on our phone pulls that code and runs it — that's
> just dev scaffolding. The running app is a **pure UI client** that calls our **Django
> backend** over Wi-Fi for all its data (`UI → API → DB`). In production, **Metro and
> Expo Go disappear**: **EAS** builds the real app, users install it from the **Play
> Store** (or use the website), and it still just calls the same backend. Same
> `client → API → DB` model you already know — Expo/Metro/Expo Go are only the
> *delivery machinery* around it.
