# DRAW & DECEIVE — Deployment Guide 🚀

Because **DRAW & DECEIVE** is a real-time multiplayer game using **Django Channels**, **WebSockets**, and **Daphne**, it requires a platform that supports persistent, long-lived bidirectional WebSocket connections.

---

## 🌟 Option 1: Render.com (Recommended — 1-Click Setup)

Render natively supports WebSockets, Python 3.12, Daphne ASGI, and managed Redis on a free tier.

We have included a pre-configured [`render.yaml`](file:///c:/Users/840%20g8/Desktop/WEB%20APP/render.yaml) blueprint in the repository.

### Steps:
1. **Push your code to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/draw-and-deceive.git
   git branch -M main
   git push -u origin main
   ```
2. Go to **[dashboard.render.com](https://dashboard.render.com/)**.
3. Click **New +** ➔ **Blueprint**.
4. Connect your GitHub repository.
5. Render reads `render.yaml` and automatically configures:
   - **Web Service**: Daphne ASGI server running `config.asgi:application`
   - **Redis Service**: Internal channel layer for real-time messaging
   - Automatic migrations & word dataset seeding
6. Click **Apply**. Your game will be live with a free `https://<your-app>.onrender.com` URL with full WebSocket support!

---

## 🚂 Option 2: Railway.app (Zero Configuration)

Railway automatically detects [`Procfile`](file:///c:/Users/840%20g8/Desktop/WEB%20APP/Procfile) and [`Dockerfile`](file:///c:/Users/840%20g8/Desktop/WEB%20APP/Dockerfile).

### Steps:
1. Push your repository to GitHub.
2. Go to **[railway.app](https://railway.app/)** and click **New Project**.
3. Select **Deploy from GitHub repo** and choose your repository.
4. Click **+ Add Service** ➔ **Database** ➔ **Redis**.
5. In your web service settings, add the environment variable:
   - `REDIS_URL`: `${{Redis.REDIS_URL}}`
   - `DJANGO_ALLOWED_HOSTS`: `*`
6. Click **Generate Domain** in the Networking tab. Your game is live!

---

## 🪰 Option 3: Fly.io (CLI Deployment)

Fly.io runs Docker containers directly near your users:

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Authenticate
fly auth login

# 3. Launch with included fly.toml & Dockerfile
fly launch

# 4. Deploy
fly deploy
```

---

## ⚠️ Notes on Vercel:
Vercel is built for serverless functions (which terminate after each HTTP request) and **does not support persistent WebSockets**. We have included [`vercel.json`](file:///c:/Users/840%20g8/Desktop/WEB%20APP/vercel.json) and [`api/index.py`](file:///c:/Users/840%20g8/Desktop/WEB%20APP/api/index.py) if you wish to host static/HTTP assets on Vercel, but for the live drawing canvas and real-time chat, use **Render**, **Railway**, or **Fly.io**.
