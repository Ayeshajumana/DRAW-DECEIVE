# DRAW & DECEIVE 🎨🎭
## Complete Real-Time Multiplayer Drawing and Guessing Game

**DRAW & DECEIVE** is a modern, full-featured multiplayer party game built with **Django**, **Django Channels**, **Daphne**, and **HTML5 Canvas**. Friends join a private room via a 6-character code or shareable invite link, take turns drawing secret words on a shared canvas, and compete to guess words in live chat before the countdown timer expires.

---

## 🌟 Key Features

- **Private Multiplayer Rooms**: Instant 6-character code generation (`7K2B9X`) with one-click copy invite links.
- **Custom Player Identities**: 16 expressive animal & fantasy avatars with customizable nicknames and career win/score tracking.
- **Real-Time Interactive Lobby**: Synchronized readiness tags, host badges, dynamic player grids, and room settings summaries.
- **High-DPI Drawing Canvas**:
  - Touch, stylus, and mouse drawing with Pointer Events (`pointerdown`, `pointermove`, `pointerup`).
  - Strict logical `800x600` coordinate normalization for identical display across desktop and mobile screens.
  - Multi-tool suite: Brush/Pencil, Eraser, Straight Line, Rectangle, Circle.
  - 16-color palette + custom color picker.
  - Adjustable brush thickness (2px, 4px, 8px, 14px, 24px) with live size indicator.
  - Undo stroke (Ctrl+Z) and Clear canvas with confirmation.
  - Throttled batch stroke transmission to minimize bandwidth.
- **Server-Authoritative Game Engine**:
  - Randomized turn rotation across rounds.
  - Secret words delivered **privately** to the active drawer only. Guessers receive progressive masked hints (`_ _ _ _`).
  - Progressive letter hints reveal automatically at 50% and 75% elapsed time.
  - Anti-cheat server validation on all stroke authoring, tool dimensions, and guess comparisons.
- **Scoring & Live Leaderboards**:
  - Guesser: 100 base points + up to 50 speed bonus points based on remaining turn time. Single-reward guard per round.
  - Drawer: 50 points per guessing opponent + 50 bonus points if all opponents guess.
  - Dynamic live leaderboard with real-time score ranking.
- **160+ Curated Words & Custom Word Packs**:
  - 8 categories: Animals, Food, Objects, Nature, Sports, Entertainment, Tech, Everyday Activities.
  - Custom user-created word packs with public/private sharing.
- **Web Audio API Sound Effects**:
  - Procedural sound synthesis (pop, correct guess chime, timer ticks, victory fanfare) with no external audio file dependencies.
- **Reconnection Recovery**: Full stroke history and game phase replayed automatically upon reconnecting.

---

## 🏗️ Architecture

```
draw_and_deceive/
│
├── config/              # Django core settings, URLs, ASGI router
│   ├── settings.py      # Daphne, Channels, Apps, Session config
│   ├── asgi.py          # ProtocolTypeRouter + SessionMiddlewareStack
│   └── urls.py          # Root URL routing
│
├── accounts/            # Session-backed player identities & avatars
│   ├── models.py        # PlayerProfile (nickname, avatar, stats)
│   ├── avatars.py       # 16 Curated SVG/emoji avatar definitions
│   └── views.py         # Profile editing & global leaderboard
│
├── rooms/               # Room management & lobby
│   ├── models.py        # GameRoom, RoomPlayer
│   ├── services.py      # Room creation, capacity checks, snapshots
│   └── views.py         # Home, Create Room, Join Room, Room view
│
├── words/               # Curated word dataset & custom packs
│   ├── models.py        # Word, WordPack, WordPackEntry
│   ├── services.py      # Normalization, hint masking, word selector
│   └── data/            # 160 curated words across 8 categories
│
├── game/                # Core real-time game engine
│   ├── models.py        # GameMatch, GameTurn, DrawingStroke, Guess
│   ├── engine.py        # Server-side state machine, turn cycle
│   ├── scoring.py       # Speed bonus & drawer point formulas
│   └── consumers.py     # Async Channels WebSocket consumer
│
├── templates/           # Django HTML5 templates
├── static/              # Vanilla CSS3 & Vanilla JavaScript
└── tests/               # 27 automated unit, WebSocket & integration tests
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- Virtual environment or package manager (`pip` or `uv`)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations & Seed Words
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_words
```

### 4. Start Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🧪 Automated Testing

Run the complete test suite (27 unit, WebSocket, and multi-player integration tests):

```bash
python manage.py test tests
```

To run individual test modules:
```bash
# Scoring calculation tests
python manage.py test tests.test_scoring

# Word normalization & hint masking tests
python manage.py test tests.test_words

# Room creation & capacity tests
python manage.py test tests.test_rooms

# Game engine & turn progression tests
python manage.py test tests.test_engine

# WebSocket consumer tests
python manage.py test tests.test_consumers

# 3-Player simulated match integration test
python manage.py test tests.test_multiplayer_integration
```

---

## 🐳 Production Deployment (Docker & Redis)

For production multi-worker environments, Redis powers the Channels communication layer:

```bash
docker-compose up --build -d
```

### Environment Variables
Configure your environment using `.env` (refer to `.env.example`):
- `DJANGO_SECRET_KEY`: Random 50+ character string.
- `DJANGO_DEBUG`: Set to `False` in production.
- `DJANGO_ALLOWED_HOSTS`: Domain names (e.g. `drawanddeceive.com,www.drawanddeceive.com`).
- `REDIS_URL`: Redis connection URL (`redis://redis:6379/0`).

---

## 📡 WebSocket Event Protocol

| Event | Direction | Description |
|---|---|---|
| `game.request_state` | Client ➔ Server | Requests full state recovery & stroke replay |
| `room.ready` | Client ➔ Server | Toggles player readiness in lobby |
| `game.start` | Client ➔ Server | Host launches match |
| `drawing.stroke` | Client ➔ Server ➔ Group | Broadcasts stroke points, tool, size & color |
| `drawing.undo` | Client ➔ Server ➔ Group | Removes drawer's last stroke |
| `drawing.clear` | Client ➔ Server ➔ Group | Clears canvas surface |
| `game.guess` | Client ➔ Server | Evaluates guess; awards points if correct |
| `game.chat` | Client ➔ Server ➔ Group | Broadcasts player chat message |
| `game.turn_started` | Server ➔ Group | Announces new round, drawer, and masked word |
| `game.secret_word` | Server ➔ Drawer | Privately delivers secret word to active drawer |
| `game.timer_update` | Server ➔ Group | Broadcasts remaining seconds countdown |
| `game.hint_update` | Server ➔ Group | Reveals progressive letters at 50% & 75% elapsed |
| `game.guess_correct` | Server ➔ Group | Celebrates correct guess & updates leaderboard |
| `game.round_results` | Server ➔ Group | Displays revealed word & round score summary |
| `game.match_results` | Server ➔ Group | Crown champion & displays final standings podium |
