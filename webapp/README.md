# Admin panel

A zero-dependency, browser-based control panel for the evaluation-faking harness. Configure the experiment and run it live — no command line needed after launch.

## Run it

```bash
# from the repo root
python3 webapp/server.py
# then open http://127.0.0.1:8000
```

That's it — the backend is Python standard library only, so there's nothing to install.

## What you can do

- **Edit the two context framings** side by side — the deployment wrapper and the evaluation wrapper. This is the core manipulation; dial the evaluation cues stronger or subtler to probe how sensitive the model is.
- **Add, edit, or remove scenarios** in a table.
- **Pick a model**, set temperature and repeats.
- **Run** and watch the observer effect, safe rates, McNemar p-value, a bar chart, and the evaluation-awareness gap update live.

## Using real models

The panel calls models server-side. Put your key in a `.env` file at the repo root (copy `.env.example`), then start the server:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The panel shows a green pill when a key is detected. **Keys are never sent to the browser** — the page only tells the server "run"; the server makes the calls. The server binds to `127.0.0.1` only, so it isn't reachable from the network.

## Files

- `server.py` — standard-library HTTP server; reuses the harness package (`providers`, `judge`, `stats`, `analyze`) and never modifies it.
- `admin.html` — the single-page UI (inline CSS/JS, inline SVG-free bar chart).
- `config.json` — generated on first run from `scenarios.jsonl`; holds your edited framings, scenarios, and settings. Git-ignored (it's your local working copy).

## Note on "fine-tuning"

This panel *configures and tunes the experiment* — framings, scenarios, model, temperature, repeats. That's different from ML "fine-tuning" (retraining a model's weights), which this project doesn't do.
