"""
Go2.Ninja - Production-Ready URL Shortener
Security hardened for deployment
"""
import os
import re
import secrets
from urllib.parse import urlparse

from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional

from .database import engine, get_db, Base
from .models import URL

# Create database tables
Base.metadata.create_all(bind=engine)

# Configuration
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
SHORT_CODE_LENGTH = 7
SHORT_CODE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
MAX_URL_LENGTH = 2048
BLOCKED_SCHEMES = {"javascript", "data", "vbscript", "file"}
RESERVED_PATHS = {"static", "api", "docs", "openapi.json", "favicon.ico", "robots.txt", "health"}

# Initialize FastAPI
app = FastAPI(
    title="Go2.Ninja",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; img-src 'self' data:;"
    return response


# Pydantic Models with Validation
class URLCreate(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        
        # Check length
        if len(v) > MAX_URL_LENGTH:
            raise ValueError(f"URL too long (max {MAX_URL_LENGTH} chars)")
        
        if len(v) < 3:
            raise ValueError("URL too short")
        
        # Add https if no scheme
        if not re.match(r'^https?://', v, re.IGNORECASE):
            v = 'https://' + v
        
        # Parse and validate URL
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError("Invalid URL format")
        
        # Block dangerous schemes (XSS prevention)
        if parsed.scheme.lower() in BLOCKED_SCHEMES:
            raise ValueError("Invalid URL scheme")
        
        # Must have valid scheme and netloc
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only HTTP/HTTPS URLs allowed")
        
        if not parsed.netloc or "." not in parsed.netloc:
            raise ValueError("Invalid domain")
        
        # Block localhost/internal IPs (SSRF prevention)
        netloc_lower = parsed.netloc.lower()
        if any(x in netloc_lower for x in ["localhost", "127.0.0.1", "0.0.0.0", "169.254", "10.", "192.168", "172.16"]):
            raise ValueError("Internal URLs not allowed")
        
        return v


class URLResponse(BaseModel):
    short_url: str
    short_code: str
    original_url: str


# Helper Functions
def generate_short_code() -> str:
    """Generate cryptographically secure short code."""
    return ''.join(secrets.choice(SHORT_CODE_CHARS) for _ in range(SHORT_CODE_LENGTH))


def validate_short_code(code: str) -> bool:
    """Validate short code format (alphanumeric only)."""
    return bool(re.match(r'^[a-zA-Z0-9]+$', code)) and len(code) <= 20


# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """Serve the main HTML page."""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Page not found")


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment."""
    return {"status": "healthy", "service": "go2.ninja"}


@app.post("/api/shorten", response_model=URLResponse)
def create_short_url(url_data: URLCreate, request: Request, db: Session = Depends(get_db)):
    """Create a shortened URL."""
    original_url = url_data.url
    
    # Check if URL already exists (prevents duplicate entries)
    existing = db.query(URL).filter(URL.original_url == original_url).first()
    if existing:
        base_url = str(request.base_url).rstrip("/")
        return URLResponse(
            short_url=f"{base_url}/{existing.short_code}",
            short_code=existing.short_code,
            original_url=original_url
        )
    
    # Generate unique short code with retry limit
    for _ in range(10):
        short_code = generate_short_code()
        if not db.query(URL).filter(URL.short_code == short_code).first():
            break
    else:
        raise HTTPException(status_code=503, detail="Service busy, try again")
    
    # Create entry (SQLAlchemy handles parameterized queries - SQL injection safe)
    db_url = URL(original_url=original_url, short_code=short_code)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    base_url = str(request.base_url).rstrip("/")
    return URLResponse(
        short_url=f"{base_url}/{short_code}",
        short_code=short_code,
        original_url=original_url
    )


@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    """Redirect to the original URL."""
    # Skip reserved paths
    if short_code.lower() in RESERVED_PATHS:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Validate short code format (prevents injection)
    if not validate_short_code(short_code):
        raise HTTPException(status_code=400, detail="Invalid short code")
    
    # Query with parameterized query (SQL injection safe)
    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Update click count
    db_url.clicks += 1
    db.commit()
    
    # Use 301 for permanent redirect (better caching)
    return RedirectResponse(url=db_url.original_url, status_code=301)
