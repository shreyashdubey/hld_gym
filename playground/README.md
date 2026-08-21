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
