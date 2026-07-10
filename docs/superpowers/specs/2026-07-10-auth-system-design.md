# Authentication & User Management System

## Overview

Add complete authentication to the SGINF Flask app: JWT login (username/password), Windows Hello (WebAuthn), and Telegram QR login. Includes user registration and per-user settings.

## Database Changes

### usuarios_sistema (recreate)
CREATE TABLE usuarios_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,          -- pbkdf2:sha256 (werkzeug generate_password_hash)
    tipo TEXT DEFAULT 'admin',
    telegram_id INTEGER,
    telegram_linked INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

### webauthn_credentials
CREATE TABLE webauthn_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES usuarios_sistema(id) ON DELETE CASCADE,
    credential_id TEXT UNIQUE NOT NULL,
    public_key TEXT NOT NULL,
    sign_count INTEGER DEFAULT 0,
    name TEXT DEFAULT 'Windows Hello',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

### auth_tokens (temporary tokens for Telegram QR login/link)
CREATE TABLE auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES usuarios_sistema(id),
    telegram_chat_id INTEGER,
    purpose TEXT NOT NULL CHECK(purpose IN ('telegram_link', 'telegram_login')),
    consumed INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

## Blueprint `auth` — API Routes

### Open (no auth required)
- POST /api/auth/login — username + senha → JWT httpOnly cookie
- POST /api/auth/webauthn/login/begin — WebAuthn login challenge
- POST /api/auth/webauthn/login/complete — verify assertion → JWT
- GET /api/auth/telegram/qrcode?purpose=login — temp token + QR data
- POST /api/auth/telegram/check — polling check if token consumed
- GET /login — login page

### Authenticated (require JWT)
- POST /api/auth/logout — clear cookie
- POST /api/auth/change-password — old + new password
- GET /api/auth/me — current user info (username, tipo, webauthn count, telegram_linked)
- POST /api/auth/webauthn/register/begin — registration challenge
- POST /api/auth/webauthn/register/complete — verify attestation
- DELETE /api/auth/webauthn/credentials/<id> — remove credential
- GET /api/auth/telegram/qrcode?purpose=link — temp token for linking
- GET /settings — settings page

### Admin-only (require JWT + tipo='admin')
- POST /api/auth/register — create new user
- GET /register — registration page

## JWT Implementation

- Library: PyJWT (pip install PyJWT)
- Algorithm: HS256
- Secret: SECRET_KEY from app config (generated via os.urandom if not set)
- Cookie name: session_token
- Cookie flags: httpOnly, Secure (prod), SameSite=Lax, Path=/
- Expiry: 8 hours
- Claims: { sub: user_id, username, tipo, iat, exp }
- CSRF: separate csrf_token cookie (non-httpOnly) + X-CSRF-Token header verified on every state-changing request

## WebAuthn (Windows Hello)

- Library: webauthn (pip install webauthn)
- Origin: window.location.origin (browser sends, verified server-side)
- RP ID: window.location.hostname
- User verification: preferred (allows PIN/biometrics)
- Attestation: none (permissive)
- Credential storage: webauthn_credentials table
- Login: filter credentials by user (if username pre-filled) or allow any

## Telegram Bot Integration

- Library: python-telegram-bot (pip install python-telegram-bot)
- Mode: polling (Updater.start_polling in a background thread)
- Bot token: stored in app config (set via environment variable TELEGRAM_BOT_TOKEN)
- Commands:
  - /start — welcome + instructions
  - /login <token> — link Telegram to pending login
  - /link <token> — link Telegram to existing account

### QR Code Login Flow
1. User clicks "Entrar com Telegram" on /login
2. GET /api/auth/telegram/qrcode?purpose=login → creates auth_tokens row, returns token + QR PNG (base64)
3. Page renders QR code
4. User scans QR with Telegram → sends /login <token> to bot
5. Bot validates token, marks consumed, stores telegram_chat_id
6. Frontend polls POST /api/auth/telegram/check { token } every 2s
7. When consumed → server looks up user by telegram_chat_id → sets JWT cookie directly in the /check response + returns { logged_in: true, redirect: '/' }
8. Frontend receives response, navigates to /

### QR Code Link Flow (Settings)
1. Same as above but purpose=link, user must be logged in
2. Backend stores user_id on the token
3. Bot validates → links telegram_chat_id to user_id permanently

## UI Pages

### /login
- Username + password form (centered card, dark theme matching existing)
- "Entrar com Windows Hello" button (shows if WebAuthn available in browser)
- "Entrar com Telegram" button → switches to QR view
- Logo + app name header

### /register (admin only)
- Username + password form
- Simple card, same style

### /settings
- Current username display
- Change password form (old + new password + confirm)
- Windows Hello section: register / remove credential
- Telegram section: link / unlink QR
- Save feedback via toast

## Dependencies (pip)
- PyJWT
- webauthn
- python-telegram-bot
- Pillow (QR code image)
- qrcode (QR generation)
- qrcode[pil] extra

## Files to Create/Modify

### New files
- app/blueprints/auth/__init__.py — Blueprint definition, all routes
- app/blueprints/auth/services.py — DB helpers, password hashing, Telegram bot thread
- app/blueprints/auth/webauthn_service.py — WebAuthn registration/verification logic
- app/blueprints/auth/telegram_bot.py — Telegram bot command handlers
- app/templates/login.html
- app/templates/register.html
- app/templates/settings.html

### Modified files
- app/__init__.py — register auth blueprint, set SECRET_KEY, init Telegram thread
- app/templates/base.html — add login/logout to nav, block unauthenticated pages
- setup_db.py — update usuarios_sistema schema, add webauthn_credentials + auth_tokens
- run.py — no changes expected
