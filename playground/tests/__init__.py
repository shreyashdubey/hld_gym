"""Test-only environment defaults.

playground/server.py reads PLAYGROUND_TOKEN_SECRET at *import* time, on
purpose -- a missing signing secret must stop the service before it serves a
request. But playground/.env is gitignored and .env.example ships the secret
commented out, so on a fresh clone importing playground.server raised and the
whole of test_server.py -- including every auth-gate, renegotiate-bypass and
cross-user-takeover test -- never ran, reported only as one collection error
among a hundred passes.

setdefault, not assignment: a real value in the environment still wins, so
this weakens nothing outside the suite. Lives in the package __init__ because
that is the only thing Python imports before the test modules themselves.
"""

import os

os.environ.setdefault("PLAYGROUND_TOKEN_SECRET", "test-only-secret-not-a-real-one")
# login() 503s when this is unset (an operator misconfiguration, not a bad
# credential). The TestLogin cases patch verify_google_id_token and are about
# what happens *past* that guard, so they need it configured; the guard itself
# gets its own test that clears it explicitly.
os.environ.setdefault("PLAYGROUND_GOOGLE_CLIENT_ID", "test-only.apps.googleusercontent.com")
