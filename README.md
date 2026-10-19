# Cloud Sentinel v2.0

Zero-cost multi-cloud SOC dashboard (mini-SIEM) with local-LLM triage and human-in-the-loop response.

## Run locally (two terminals)

**Backend** (FastAPI, Python 3.13):

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

**Frontend** (React + Vite + Tailwind):

```powershell
cd frontend
npm run dev
```

Open http://localhost:5173. Vite proxies `/api/*` to the backend on port 8000.

Fresh setup: `py -3.13 -m venv backend\.venv`, then `pip install -r backend\requirements.txt`, and `npm install` in `frontend`.

## Local LLM (Ollama)

Incident briefings ("why it was flagged" + playbook preview) come from a local model:

```powershell
winget install Ollama.Ollama      # once; Ollama then runs in the background
ollama pull llama3.1:8b           # once, ~4.9 GB
```

The backend loads the model at startup and generates briefings in the background as soon as an
incident is created or gains events (about 10-15 s each on an RTX 4050). If Ollama is not running,
a rule-based briefing is shown instead, labelled as such, so the demo never stalls.

Settings (environment variables, optional):

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama server |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model; `mistral:7b` also works |
| `OLLAMA_NUM_GPU` | `99` | Layers on GPU. Forced high because Ollama's default leaves 25% of the model on the CPU on a 6 GB GPU (3x slower). Lower it if you see out-of-memory errors. |
| `OLLAMA_NUM_CTX` | `3072` | Context window; fits 10 events of evidence plus the answer |

Before presenting: start the backend a minute early so the model is loaded, and open one incident
to confirm the footer says "Generated locally by llama3.1:8b".

## Demo data

With the backend running, push synthetic attack findings from a third terminal:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python inject.py ddos          # AWS: Shield DDoS on a load balancer + WAF rate-limit hits
python inject.py brute-force   # Azure RDP brute force, then the same IP on GCP SSH (multi-cloud incident)
python inject.py misconfig     # public GCP bucket, public S3 bucket, Azure public blob access
python inject.py all           # all three
python inject.py reset         # clear everything before a presentation
```

`--delay 1` slows the stream so the dashboard fills visibly. All IPs and account IDs are synthetic (RFC 5737 ranges, AWS example account).

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness |
| GET | `/api/summary` | Per-provider 24 h counts, incidents awaiting clearance |
| GET | `/api/events?limit=50` | Newest normalized events |
| POST | `/api/events` | Ingest `{channel, events: [...]}` (injection scripts, later cloud pollers) |
| GET | `/api/incidents?include_resolved=false` | Incidents, awaiting-clearance first |
| GET | `/api/incidents/{id}` | One incident with its events |
| GET | `/api/incidents/{id}/briefing?refresh=false` | LLM briefing; `state` is `ready`, `updating` or `generating` (poll until `ready`) |
| GET | `/api/llm/status` | Whether Ollama is reachable and the model is installed |
| POST | `/api/incidents/{id}/decisions` | Analyst decision `{action: investigate\|keep_open\|resolve, comment, analyst}`; the only way status changes |
| GET | `/api/incidents/{id}/decisions` | Decision history for one incident |
| GET | `/api/audit` | Every decision, newest first |
| POST | `/api/admin/reset` | Clear all data |

Interactive docs: http://127.0.0.1:8000/docs. The event schema lives in `backend/schemas.py`.

### Human oversight rules (`backend/store.py`)

- Incidents start as `new` (**HOLD**). Only an analyst decision changes the status:
  Investigate → `investigating`, Keep open → `open`, Resolve → `resolved`.
- Every decision needs an analyst name and a comment of at least 10 characters (whitespace doesn't count).
- Re-applying the current status is rejected (409); a resolved incident is closed for good, and new
  activity from the same source opens a new incident.
- Decisions are written to an append-only `decisions` table: a SQLite trigger rejects any UPDATE.
  Each row records the status before and after, and which briefing (model or rule-based, and when)
  was on screen, so AI advice and human judgement can be compared afterwards.
- Playbook steps are never executed by the system; the analyst records which ones they approved in the comment.

### Correlation rules (`backend/store.py`)

- Events correlate on attacker IP when present, otherwise on the resource.
- A high or critical event opens an incident with status `new` (shown as **HOLD**, awaiting analyst clearance).
- Five low/medium events with the same category and key within 10 minutes escalate into an incident.
- Later matching events within 60 minutes attach to the open incident; if they come from another cloud it becomes a **Multi-cloud** incident.
