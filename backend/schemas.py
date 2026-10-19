"""Normalized security alert schema shared by injection scripts and cloud pollers."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

Provider = Literal["aws", "gcp", "azure"]
Severity = Literal["low", "medium", "high", "critical"]
Category = Literal[
    "ddos",
    "brute_force",
    "misconfiguration",
    "malware",
    "anomalous_access",
    "other",
]
IncidentStatus = Literal["new", "investigating", "open", "resolved"]
IngestChannel = Literal["injection", "poll"]

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class EventIn(BaseModel):
    """One finding from a cloud security hub, normalized to a common shape."""

    provider: Provider
    source: str = Field(description="Native service, e.g. 'Security Hub'")
    category: Category
    severity: Severity
    title: str
    description: str = ""
    resource: str = Field(description="ARN, resource name, or resource ID the finding is about")
    region: str | None = None
    actor_ip: str | None = Field(default=None, description="Source IP of the activity, when known")
    native_id: str | None = Field(default=None, description="The provider's own finding ID")
    observed_at: datetime | None = Field(default=None, description="When the provider saw it; defaults to now")
    raw: dict[str, Any] = Field(default_factory=dict, description="Original provider payload")


class Event(EventIn):
    id: str
    observed_at: datetime
    ingested_at: datetime
    channel: IngestChannel
    incident_id: str | None = None


class IngestRequest(BaseModel):
    channel: IngestChannel = "injection"
    events: list[EventIn] = Field(min_length=1, max_length=500)


class IngestResult(BaseModel):
    accepted: int
    incidents_created: int
    incidents_updated: int
    incident_ids: list[str]  # every incident created or updated by this batch


class Incident(BaseModel):
    id: str
    title: str
    category: Category
    severity: Severity
    status: IncidentStatus
    providers: list[Provider]
    correlation_key: str
    event_count: int
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime


class IncidentDetail(Incident):
    events: list[Event]


DecisionAction = Literal["investigate", "keep_open", "resolve"]

# Each analyst action moves the incident to exactly one status.
ACTION_STATUS: dict[str, str] = {"investigate": "investigating", "keep_open": "open", "resolve": "resolved"}


class DecisionIn(BaseModel):
    action: DecisionAction
    # Whitespace is stripped before the length check, so blank padding can't satisfy it.
    comment: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)] = Field(
        description="Required justification"
    )
    analyst: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]


class Decision(BaseModel):
    id: str
    incident_id: str
    incident_title: str
    action: DecisionAction
    comment: str
    analyst: str
    from_status: IncidentStatus
    to_status: IncidentStatus
    # What advice the analyst had in front of them when deciding.
    briefing_generator: Literal["llm", "template"] | None
    briefing_model: str | None
    briefing_generated_at: str | None
    decided_at: datetime


class ProviderSummary(BaseModel):
    events_24h: int
    last_event_at: datetime | None
    # Phase 6 pollers will set this; until then only injected data exists.
    connected: bool
    channel: IngestChannel | None


class Summary(BaseModel):
    providers: dict[Provider, ProviderSummary]
    awaiting_clearance: int
    open_incidents: int
