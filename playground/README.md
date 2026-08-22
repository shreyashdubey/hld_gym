# playground — the voice service

The fourth pipeline. Runs Pipecat over a self-hosted WebRTC connection and holds
the OpenAI key. The client lives in `sell/app/playground/`.

```bash
cd playground
uv venv .venv
VIRTUAL_ENV=$PWD/.venv uv pip install -r pyproject.toml
VIRTUAL_ENV=$PWD/.venv uv pip install httpx
cp .env.example .env      # put a real key in it
cd ..
playground/.venv/bin/uvicorn playground.server:app --reload --port 7860 --app-dir .
playground/.venv/bin/python -m unittest discover -s playground/tests -t .
```

Deployment is deliberately undecided — see the spec's "Deliberately unresolved".

## Auth

`mode=playground` and `mode=diagnostic` on `POST /api/offer` require a Google sign-in; `mode=dictation`
needs nothing and stays completely open — see `playground/auth.py` and
`AGENTS.md`'s hard rules for why. Two env vars, both already in `.env`:

- **`PLAYGROUND_GOOGLE_CLIENT_ID`** — a Google OAuth client ID. Public by
  design: it identifies this app to Google and authorizes nothing by itself,
  so it's safe to commit and it also has to reach the browser. `sell/` is a
  static export with no server, so the same value has to be baked in at
  build time too:
  ```
  # sell/.env.local (gitignored via sell/.env*)
  NEXT_PUBLIC_PLAYGROUND_GOOGLE_CLIENT_ID=<the same client ID>
  ```
  Get a client ID from the Google Cloud Console → *APIs & Services* →
  *Credentials* → *Create OAuth client ID* → *Web application*, with this
  service's origins (`http://localhost:3000` in dev) under *Authorized
  JavaScript origins*. **Only the client ID is exposed this way — never
  `PLAYGROUND_TOKEN_SECRET`, never `OPENAI_API_KEY`.** Neither of those may
  ever be prefixed `NEXT_PUBLIC_*`.

- **`PLAYGROUND_TOKEN_SECRET`** — signs and verifies this service's own
  session tokens (not Google's; see `playground/auth.py` for the format,
  deliberately not JWT). Secret, with **no default**: the service refuses to
  start without it, the same way `_allowed_origins()` in `server.py` refuses
  a `*` wildcard, because a default signing secret would mean anyone could
  forge a session. Generate one with:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  **To rotate it** (a leaked secret, or just periodically): replace the
  value in `playground/.env` and restart the service. Every token signed
  under the old secret stops verifying immediately — everyone is signed out
  at once, with no partial state to clean up, and a learner mid-round loses
  nothing beyond needing to sign in again on their next `/api/offer` call.
  There is no allowlist beyond "has a Google account" — see
  `sell/PROGRESS.md`'s 2026-08-22 entry for why that's an accepted trade,
  and what would make it stop being one.

- `PLAYGROUND_SESSION_TTL_SECS` (optional, default `604800` = 7 days) — how
  long our own token lasts before a learner has to sign in with Google
  again.
