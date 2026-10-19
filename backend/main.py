from contextlib import asynccontextmanager
from datetime import datetime, timezone

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import briefing_worker
import llm
import store
from schemas import (
    Decision,
    DecisionIn,
    Event,
    Incident,
    IncidentDetail,
    IngestRequest,
    IngestResult,
    Summary,
)


class BriefingResponse(BaseModel):
    state: Literal["ready", "updating", "generating"]
    briefing: llm.Briefing | None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init_db()
    llm.warm_up()
    briefing_worker.start()
    yield


app = FastAPI(title="Cloud Sentinel API", version="2.0.0", lifespan=lifespan)

# The Vite dev server proxies /api, but allow direct calls from it too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "cloud-sentinel-backend",
        "version": app.version,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/summary", response_model=Summary)
def get_summary():
    return store.summary()


@app.get("/api/events", response_model=list[Event])
def get_events(limit: int = Query(50, ge=1, le=500)):
    return store.list_events(limit)


@app.post("/api/events", response_model=IngestResult, status_code=201)
def ingest_events(body: IngestRequest):
    result = store.ingest(body.events, body.channel)
    for incident_id in result.incident_ids:
        briefing_worker.enqueue(incident_id)
    return result


@app.get("/api/incidents", response_model=list[Incident])
def get_incidents(include_resolved: bool = False):
    return store.list_incidents(include_resolved)


@app.get("/api/incidents/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: str):
    found = store.get_incident(incident_id)
    if not found:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident, events = found
    return IncidentDetail(**incident.model_dump(), events=events)


@app.get("/api/incidents/{incident_id}/briefing", response_model=BriefingResponse)
def get_briefing(incident_id: str, refresh: bool = False):
    """Why the incident was flagged plus a playbook preview, generated in the background.

    state is 'ready' when the briefing matches the current evidence, 'updating' when an
    older briefing is shown while a new one is generated, and 'generating' when none exists
    yet. Clients poll until 'ready'. A rule-based briefing (model unavailable) counts as
    ready; ask for refresh=true to retry the model.
    """
    found = store.get_incident(incident_id)
    if not found:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident, _events = found

    cached = store.get_briefing(incident_id)
    if refresh:
        briefing_worker.enqueue(incident_id, force=True)
    elif not cached or cached[0] != incident.event_count:
        briefing_worker.enqueue(incident_id)

    if briefing_worker.is_pending(incident_id):
        state = "updating" if cached else "generating"
    else:
        state = "ready" if cached else "generating"
    return {"state": state, "briefing": cached[2] if cached else None}


@app.post("/api/incidents/{incident_id}/decisions", response_model=Decision, status_code=201)
def decide(incident_id: str, body: DecisionIn):
    """Record an analyst decision. This is the only way an incident's status changes."""
    try:
        decision = store.record_decision(incident_id, body)
    except store.DecisionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not decision:
        raise HTTPException(status_code=404, detail="Incident not found")
    return decision


@app.get("/api/incidents/{incident_id}/decisions", response_model=list[Decision])
def incident_decisions(incident_id: str):
    return store.list_decisions(incident_id)


@app.get("/api/audit", response_model=list[Decision])
def audit_log(limit: int = Query(200, ge=1, le=1000)):
    return store.list_decisions(limit=limit)


@app.get("/api/llm/status")
def llm_status():
    return llm.status()


@app.post("/api/admin/reset", status_code=204)
def reset():
    store.reset_db()
