"""Background queue that pre-generates incident briefings.

A briefing takes ~10-15 s on a laptop GPU, so it is generated as soon as an incident is
created or gains new events. By the time an analyst opens the incident it is usually ready.
One worker thread runs at a time because the local model serves one request at a time anyway.
"""

import queue
import threading
from datetime import datetime, timezone

import llm
import store

_queue: "queue.Queue[tuple[str, bool]]" = queue.Queue()
_pending: set[str] = set()
_lock = threading.Lock()


def enqueue(incident_id: str, force: bool = False) -> None:
    with _lock:
        if incident_id in _pending:
            return
        _pending.add(incident_id)
    _queue.put((incident_id, force))


def is_pending(incident_id: str) -> bool:
    with _lock:
        return incident_id in _pending


def is_fresh(cached, event_count: int) -> bool:
    """A briefing is current when the model wrote it for the incident's present evidence."""
    return bool(cached) and cached[0] == event_count and cached[1] == "llm"


def _run() -> None:
    while True:
        incident_id, force = _queue.get()
        try:
            found = store.get_incident(incident_id)
            if not found:
                continue
            incident, events = found
            if not force and is_fresh(store.get_briefing(incident_id), incident.event_count):
                continue
            briefing = llm.generate(incident, events, datetime.now(timezone.utc).isoformat())
            store.save_briefing(incident_id, incident.event_count, briefing.generator, briefing.model_dump())
        except Exception:  # keep the worker alive; the next request re-queues the incident
            pass
        finally:
            with _lock:
                _pending.discard(incident_id)


def start() -> None:
    threading.Thread(target=_run, daemon=True, name="briefing-worker").start()
    # Catch up on incidents that arrived while the backend (or the model) was down.
    for incident in store.list_incidents(include_resolved=False):
        if not is_fresh(store.get_briefing(incident.id), incident.event_count):
            enqueue(incident.id)
