# Go2.Ninja

A URL shortener built with Python.

## How It Works

URL shortening is simple: take a long URL, generate a short code, store the mapping, and redirect visitors.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Architecture                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   User: google.com/very/long/path                              │
│            │                                                    │
│            ▼                                                    │
│   ┌─────────────────┐                                          │
│   │   POST /api/    │  1. Validate URL                         │
│   │   shorten       │  2. Generate 7-char code (base62)        │
│   │                 │  3. Store in PostgreSQL                  │
│   └────────┬────────┘                                          │
│            │                                                    │
│            ▼                                                    │
│   Response: go2.ninja/abc123                                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Visitor clicks: go2.ninja/abc123                             │
│            │                                                    │
│            ▼                                                    │
│   ┌─────────────────┐                                          │
│   │  GET /{code}    │  1. Lookup code in DB                    │
│   │                 │  2. Increment click counter              │
│   │                 │  3. 301 Redirect                         │
│   └────────┬────────┘                                          │
│            │                                                    │
│            ▼                                                    │
│   Redirects to: google.com/very/long/path                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Short Code Generation

7 alphanumeric characters (a-z, A-Z, 0-9) = 62^7 = **3.5 trillion** possible URLs.

### Tech Stack

- **FastAPI** - Python web framework
- **PostgreSQL** - Database (Aiven)  
- **SQLAlchemy** - ORM
- **Uvicorn** - ASGI server

## Run Locally

```bash
# Clone
git clone https://github.com/utsav-pal/go2.ninja.git
cd go2.ninja

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Run
uvicorn app.main:app --reload
```

Open http://localhost:8000

## API

```bash
# Shorten URL
curl -X POST http://localhost:8000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Response
{"short_url": "http://localhost:8000/abc123", "short_code": "abc123", "original_url": "https://example.com"}
```

## Deploy

Push to GitHub, connect to Railway, add `DATABASE_URL` env var.

## License

MIT

---

Made by [Utsav Pal](https://github.com/utsav-pal)
