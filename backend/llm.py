"""Incident briefings from a local Ollama model, with a rule-based fallback.

The model explains why an incident was flagged and previews a response playbook.
Nothing here executes an action: the playbook is advice for the analyst, who decides
in the oversight workflow.
"""

import json
import os
import threading
from urllib import error, request

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, ValidationError

from schemas import Event, Incident

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
TIMEOUT_S = 120  # the first call loads the model onto the GPU
# Ollama's memory estimate is conservative and leaves ~25% of an 8B model on the CPU
# on a 6 GB laptop GPU (3x slower). Forcing all layers onto the GPU with a context that
# fits the prompt (~1.6k tokens for 10 events) plus the answer runs it at full speed.
MODEL_OPTIONS = {
    "num_ctx": int(os.environ.get("OLLAMA_NUM_CTX", "3072")),
    "num_gpu": int(os.environ.get("OLLAMA_NUM_GPU", "99")),
}
MAX_EVENTS = 10
MAX_RAW_CHARS = 600

# MITRE ATT&CK mapping is deterministic so the model can't misattribute it.
TECHNIQUES = {
    "ddos": ("T1498", "Network Denial of Service"),
    "brute_force": ("T1110", "Brute Force"),
    "misconfiguration": ("T1530", "Data from Cloud Storage"),
    "malware": ("T1204", "User Execution"),
    "anomalous_access": ("T1078", "Valid Accounts"),
    "other": (None, None),
}


Sentence = Annotated[str, StringConstraints(min_length=25, max_length=400)]


class PlaybookStep(BaseModel):
    action: Annotated[str, StringConstraints(min_length=10, max_length=200)] = Field(
        description="One concrete response action, imperative voice"
    )
    rationale: Sentence = Field(description="Why this step, tied to the evidence")
    reversible: bool = Field(description="True if the step can be undone without data loss")


class BriefingContent(BaseModel):
    summary: Sentence = Field(description="One sentence: what is happening and where")
    why_flagged: list[Sentence] = Field(min_length=2, max_length=5, description="Evidence-based reasons")
    risk_if_ignored: Sentence
    playbook: list[PlaybookStep] = Field(min_length=3, max_length=6)
    confidence: str = Field(pattern="^(low|medium|high)$")


class Briefing(BriefingContent):
    incident_id: str
    technique_id: str | None
    technique_name: str | None
    generator: str  # "llm" or "template"
    model: str | None
    event_count: int
    generated_at: str


SYSTEM_PROMPT = """You are a cloud security analyst assistant inside a SOC dashboard.
You brief a human analyst on one incident. Rules:
- Use ONLY the evidence provided. Never invent IPs, resources, accounts, counts or times.
- Quote concrete evidence (resource names, IPs, counts, providers) in why_flagged.
- The playbook is a PREVIEW for the analyst to approve or reject. Nothing is executed.
  Prefer containment steps that are reversible; mark irreversible steps reversible=false.
- If several clouds are involved, say so and explain the cross-cloud link.
- Be terse and operational. No marketing language, no greetings.

Fields:
- summary: one full sentence naming the activity, the target and the cloud(s).
- why_flagged: 2-5 full sentences, each one piece of evidence and why it matters,
  e.g. "455 failed RDP sign-ins from 203.0.113.47 hit jump-host-01 within minutes,
  far above normal admin activity." Never a bare IP, hostname or region.
- risk_if_ignored: one or two sentences on the concrete consequence, not a rating.
- playbook: 3-6 ordered steps, most urgent containment first.
  reversible=false ONLY when the step destroys or replaces something that cannot be put
  back: rotating or resetting credentials or keys, deleting data or resources, terminating
  instances. Blocking, restricting, scaling, monitoring, reviewing and investigating are
  reversible=true.
- confidence: low, medium or high, based on how strong the evidence is.
Respond with JSON only, matching the provided schema."""


def _trim_raw(raw: dict) -> str:
    text = json.dumps(raw, separators=(",", ":"))
    return text if len(text) <= MAX_RAW_CHARS else text[:MAX_RAW_CHARS] + "…"


def _prompt(incident: Incident, events: list[Event]) -> str:
    technique_id, technique_name = TECHNIQUES[incident.category]
    lines = [
        f"Incident: {incident.title}",
        f"Category: {incident.category}; severity: {incident.severity}; status: {incident.status}",
        f"Providers: {', '.join(incident.providers)}",
        f"Correlated on: {incident.correlation_key}",
        f"Events: {incident.event_count}; first seen {incident.first_seen.isoformat()}; "
        f"last seen {incident.last_seen.isoformat()}",
    ]
    if technique_id:
        lines.append(f"MITRE ATT&CK technique (fixed, do not change): {technique_id} {technique_name}")
    lines.append("")
    lines.append(f"Evidence (up to {MAX_EVENTS} events, oldest first):")
    # Raw payloads are long; include one per distinct finding type to keep the prompt small.
    raw_seen = set()
    for e in events[-MAX_EVENTS:]:
        line = (
            f"- [{e.observed_at.isoformat()}] {e.provider}/{e.source} {e.severity}: {e.title}. "
            f"{e.description} Resource: {e.resource}. Region: {e.region or 'n/a'}. "
            f"Actor IP: {e.actor_ip or 'n/a'}."
        )
        if e.title not in raw_seen:
            raw_seen.add(e.title)
            line += f" Raw: {_trim_raw(e.raw)}"
        lines.append(line)
    return "\n".join(lines)


def _call_ollama(path: str, body: dict, timeout: float) -> dict:
    req = request.Request(
        f"{OLLAMA_URL}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read())


def _generate_llm(incident: Incident, events: list[Event]) -> BriefingContent:
    response = _call_ollama(
        "/api/chat",
        {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _prompt(incident, events)},
            ],
            "format": BriefingContent.model_json_schema(),
            "stream": False,
            "keep_alive": "30m",
            "options": {**MODEL_OPTIONS, "temperature": 0.2},
        },
        TIMEOUT_S,
    )
    return BriefingContent.model_validate_json(response["message"]["content"])


# Rule-based fallback --------------------------------------------------------

TEMPLATE_PLAYBOOKS = {
    "ddos": [
        ("Confirm AWS Shield / WAF mitigation is engaged on the targeted resource", "Verifies automatic protection is absorbing the flood", True),
        ("Tighten the WAF rate-based rule threshold for the affected listener", "Reduces per-source request volume reaching the origin", True),
        ("Scale out the target group behind the load balancer", "Preserves availability while mitigation settles", True),
        ("Open a case with the provider's DDoS response team if errors persist", "Escalates to specialists with network-level visibility", True),
    ],
    "brute_force": [
        ("Block the source IP at the network security group / firewall on every affected cloud", "Stops further attempts from the correlated actor", True),
        ("Restrict RDP/SSH to a bastion or just-in-time access", "Removes the exposed management port as an entry point", True),
        ("Reset credentials for accounts targeted by the attempts", "Invalidates any password the actor may have guessed", False),
        ("Review sign-in and session logs on hosts reporting a successful login", "Determines whether the actor gained access", True),
    ],
    "misconfiguration": [
        ("Remove public access (allUsers / Principal '*' / public blob access) from the resource", "Closes the exposure immediately", True),
        ("Enable the account-level public access block for storage", "Prevents the same misconfiguration recurring", True),
        ("Review access logs for anonymous reads during the exposure window", "Determines whether data was actually accessed", True),
        ("Notify the data owner and record the exposure for compliance review", "Starts any required disclosure process", True),
    ],
}
GENERIC_PLAYBOOK = [
    ("Review the correlated events and affected resources", "Establishes scope before acting", True),
    ("Contain the affected resource with a reversible control", "Limits impact while investigating", True),
    ("Escalate to the resource owner", "Brings in context the SOC lacks", True),
]


def _generate_template(incident: Incident, events: list[Event]) -> BriefingContent:
    target = incident.correlation_key.split(":", 1)[1]
    clouds = " and ".join(p.upper() for p in incident.providers)
    reasons = [
        f"{incident.event_count} {incident.category.replace('_', ' ')} event(s) correlated on {target}",
        f"Highest reported severity is {incident.severity}",
    ]
    if len(incident.providers) > 1:
        reasons.append(f"The same indicator appears on {clouds}, suggesting one actor across clouds")
    reasons.extend(list(dict.fromkeys(e.title for e in events))[:2])
    steps = TEMPLATE_PLAYBOOKS.get(incident.category, GENERIC_PLAYBOOK)
    return BriefingContent(
        summary=f"{incident.title} on {clouds}.",
        why_flagged=reasons[:5],
        risk_if_ignored="The activity may continue or escalate; review the evidence and decide on containment.",
        playbook=[PlaybookStep(action=a, rationale=r, reversible=rev) for a, r, rev in steps],
        confidence="medium",
    )


def generate(incident: Incident, events: list[Event], generated_at: str) -> Briefing:
    technique_id, technique_name = TECHNIQUES[incident.category]
    content, generator, model = None, "template", None
    for _attempt in range(2):  # one retry if the model's JSON misses the schema
        try:
            content, generator, model = _generate_llm(incident, events), "llm", OLLAMA_MODEL
            break
        except (ValidationError, json.JSONDecodeError, KeyError):
            continue
        except (error.URLError, TimeoutError, OSError):
            break  # Ollama unreachable: no point retrying
    if content is None:
        content = _generate_template(incident, events)
    return Briefing(
        **content.model_dump(),
        incident_id=incident.id,
        technique_id=technique_id,
        technique_name=technique_name,
        generator=generator,
        model=model,
        event_count=incident.event_count,
        generated_at=generated_at,
    )


def warm_up() -> None:
    """Load the model onto the GPU in the background so the first briefing is fast."""

    def _load():
        try:
            # Same options as generation, or Ollama reloads the model on the first briefing.
            _call_ollama(
                "/api/generate",
                {"model": OLLAMA_MODEL, "keep_alive": "30m", "options": MODEL_OPTIONS},
                TIMEOUT_S,
            )
        except (error.URLError, TimeoutError, OSError):
            pass  # Ollama offline: briefings fall back to templates.

    threading.Thread(target=_load, daemon=True).start()


def status() -> dict:
    try:
        tags = _call_ollama_get("/api/tags")
    except (error.URLError, TimeoutError, OSError):
        return {"available": False, "model": OLLAMA_MODEL, "model_installed": False}
    names = {m["name"] for m in tags.get("models", [])}
    return {"available": True, "model": OLLAMA_MODEL, "model_installed": OLLAMA_MODEL in names}


def _call_ollama_get(path: str) -> dict:
    with request.urlopen(f"{OLLAMA_URL}{path}", timeout=3) as res:
        return json.loads(res.read())
