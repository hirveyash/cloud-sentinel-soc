# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: a SOC analyst triaging cloud security findings at a desk over long sessions. They need dense, fast-scanning information and confidence about which incidents need a human decision. Secondary: a Master's capstone panel watching a live demo of the same tool.

## Product Purpose

Cloud Sentinel is a zero-cost mini-SIEM. It pulls findings from the native security hubs of free-tier AWS, GCP, and Azure accounts into one dashboard, uses a locally hosted LLM to explain why each alert was flagged and preview a response playbook, and requires an analyst to make an explicit, commented decision (Investigate, Keep Open, Resolve) before any response is logged. Success means an analyst can see the multi-cloud posture at a glance and every response action has an auditable human decision behind it.

## Positioning

Multi-cloud correlation plus strict, auditable human-in-the-loop oversight, with all AI reasoning done by a local model (Ollama), so no finding leaves the machine and nothing costs money.

## Operating Context

- Runs locally on Windows: FastAPI backend (port 8000), React + Vite + Tailwind 4 frontend (port 5173), SQLite, Ollama.
- Data comes from cloud SDK polling (Boto3, Google Cloud, Azure) or from Python injection scripts that push realistic attack payloads (DDoS, brute force, misconfiguration) to guarantee a reliable live demo.
- Core screens: the dashboard (status banner, per-provider event counts, Live Incidents, Security Events) and the Incident Detail screen (LLM explanation, playbook preview, decision buttons, analyst comment).

## Capabilities and Constraints

- Must work fully offline: no external fonts, CDNs, or remote assets.
- Incident statuses and analyst actions: Investigate, Keep Open, Resolve; every action needs a comment and is persisted.
- Providers: AWS, GCP, Azure only.
- The alert JSON schema is undecided (Phase 3).

## Brand Commitments

- Name: "Cloud Sentinel v2.0".
- Voice: operational and terse, like real SOC tooling. Short labels, precise status words, no marketing language.

## Evidence on Hand

No real findings or incident data yet. Never fabricate counts or incidents in the UI; show honest empty or zero states until the backend supplies data.

## Product Principles

1. The human decides: the UI never implies an action happened without an analyst's recorded decision.
2. Severity and status must be readable at a glance; density serves scanning, not decoration.
3. Show the truth: no fake data, and empty, loading, and offline states are first-class.
4. One pane across three clouds: providers are peers, compared side by side.
