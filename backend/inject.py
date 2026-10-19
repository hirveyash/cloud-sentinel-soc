"""Push realistic "bad actor" findings into Cloud Sentinel for a reliable live demo.

Each scenario sends normalized events plus a raw payload shaped like the provider's
native finding (AWS Security Hub ASFF, GCP Security Command Center, Microsoft Defender
for Cloud). All IPs, account IDs and resource names are synthetic: IPs come from the
RFC 5737 documentation ranges.

Usage:
    python inject.py ddos
    python inject.py brute-force
    python inject.py misconfig
    python inject.py all
    python inject.py reset
Options:
    --api URL      backend base URL (default http://127.0.0.1:8000)
    --delay SECS   pause between events so the dashboard fills live (default 0.4)
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib import error, request

AWS_ACCOUNT = "123456789012"
GCP_PROJECT = "sentinel-demo-prod"
AZURE_SUB = "00000000-0000-4000-8000-000000000001"

ATTACKER_IP = "203.0.113.47"  # brute force, seen on Azure and then GCP


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Native payload builders -----------------------------------------------------

def asff(finding_type: str, title: str, label: str, resource_type: str, resource_id: str, region: str) -> dict:
    return {
        "SchemaVersion": "2018-10-08",
        "Id": f"arn:aws:securityhub:{region}:{AWS_ACCOUNT}:finding/{uuid.uuid4()}",
        "ProductArn": f"arn:aws:securityhub:{region}::product/aws/securityhub",
        "AwsAccountId": AWS_ACCOUNT,
        "Types": [finding_type],
        "CreatedAt": now_iso(),
        "Severity": {"Label": label},
        "Title": title,
        "Resources": [{"Type": resource_type, "Id": resource_id, "Region": region}],
        "Workflow": {"Status": "NEW"},
        "RecordState": "ACTIVE",
    }


def scc(category: str, resource_name: str, severity: str, finding_class: str = "THREAT", **extra) -> dict:
    return {
        "name": f"organizations/000000000000/sources/0000/findings/{uuid.uuid4().hex}",
        "parent": "organizations/000000000000/sources/0000",
        "resourceName": resource_name,
        "state": "ACTIVE",
        "category": category,
        "severity": severity,
        "findingClass": finding_class,
        "eventTime": now_iso(),
        **extra,
    }


def defender(alert_type: str, name: str, severity: str, entity: str, **properties) -> dict:
    return {
        "id": f"/subscriptions/{AZURE_SUB}/providers/Microsoft.Security/locations/eastus/alerts/{uuid.uuid4()}",
        "properties": {
            "alertType": alert_type,
            "alertDisplayName": name,
            "severity": severity,
            "compromisedEntity": entity,
            "status": "Active",
            "timeGeneratedUtc": now_iso(),
            "extendedProperties": properties,
        },
    }


# Scenarios -------------------------------------------------------------------

def ddos() -> list[dict]:
    alb = f"arn:aws:elasticloadbalancing:us-east-1:{AWS_ACCOUNT}:loadbalancer/app/storefront-alb/50dc6c495c0c9188"
    events = [{
        "provider": "aws",
        "source": "Security Hub",
        "category": "ddos",
        "severity": "critical",
        "title": "DDoS attack detected on storefront-alb",
        "description": "AWS Shield detected a volumetric HTTP flood against the storefront load balancer "
                       "(peak 1.8M requests/min, 40x baseline).",
        "resource": alb,
        "region": "us-east-1",
        "raw": asff("TTPs/Impact/Network Denial of Service", "DDoS attack detected", "CRITICAL",
                    "AwsElbv2LoadBalancer", alb, "us-east-1"),
    }]
    for i, ip in enumerate(["198.51.100.12", "198.51.100.87", "203.0.113.201", "198.51.100.140"]):
        events.append({
            "provider": "aws",
            "source": "Security Hub",
            "category": "ddos",
            "severity": "medium",
            "title": "WAF rate-based rule blocked flood traffic",
            "description": f"AWS WAF rule RateLimit-2000 blocked {12_000 + i * 3_100} requests in 5 minutes.",
            "resource": alb,
            "region": "us-east-1",
            "raw": asff("TTPs/Impact/Network Denial of Service", "Rate-based rule triggered", "MEDIUM",
                        "AwsElbv2LoadBalancer", alb, "us-east-1") | {"Network": {"SourceIpV4": ip}},
        })
    return events


def brute_force() -> list[dict]:
    vm = f"/subscriptions/{AZURE_SUB}/resourceGroups/prod-rg/providers/Microsoft.Compute/virtualMachines/jump-host-01"
    events = []
    for attempts in (40, 85, 130, 210, 320, 455):
        events.append({
            "provider": "azure",
            "source": "Defender for Cloud",
            "category": "brute_force",
            "severity": "medium",
            "title": "Failed RDP sign-ins on jump-host-01",
            "description": f"{attempts} failed RDP authentication attempts from {ATTACKER_IP} "
                           "against accounts administrator, admin, azureuser.",
            "resource": vm,
            "region": "eastus",
            "actor_ip": ATTACKER_IP,
            "raw": defender("VM_RDPBruteForce", "Failed RDP brute force attack", "Medium", "jump-host-01",
                            attackerIp=ATTACKER_IP, failedAttempts=str(attempts)),
        })
    # Same IP pivots to GCP: this is the cross-cloud correlation the dashboard shows.
    instance = f"//compute.googleapis.com/projects/{GCP_PROJECT}/zones/us-central1-a/instances/bastion-gcp"
    events.append({
        "provider": "gcp",
        "source": "Security Command Center",
        "category": "brute_force",
        "severity": "high",
        "title": "Brute force: SSH on bastion-gcp",
        "description": f"Successful SSH login to bastion-gcp after 212 failed attempts from {ATTACKER_IP}.",
        "resource": instance,
        "region": "us-central1",
        "actor_ip": ATTACKER_IP,
        "raw": scc("Brute force: SSH", instance, "HIGH",
                   access={"callerIp": ATTACKER_IP, "methodName": "ssh"}),
    })
    return events


def misconfig() -> list[dict]:
    bucket_gcp = f"//storage.googleapis.com/{GCP_PROJECT}-customer-exports"
    bucket_aws = f"arn:aws:s3:::acme-payroll-archive-{AWS_ACCOUNT}"
    storage_az = f"/subscriptions/{AZURE_SUB}/resourceGroups/prod-rg/providers/Microsoft.Storage/storageAccounts/acmelogsprod"
    return [
        {
            "provider": "gcp",
            "source": "Security Command Center",
            "category": "misconfiguration",
            "severity": "high",
            "title": "Public bucket ACL on customer-exports",
            "description": "Bucket grants storage.objectViewer to allUsers; 1,240 objects are publicly readable.",
            "resource": bucket_gcp,
            "region": "us",
            "raw": scc("PUBLIC_BUCKET_ACL", bucket_gcp, "HIGH", finding_class="MISCONFIGURATION"),
        },
        {
            "provider": "aws",
            "source": "Security Hub",
            "category": "misconfiguration",
            "severity": "critical",
            "title": "S3 bucket allows public read: acme-payroll-archive",
            "description": "Block Public Access is disabled and the bucket policy grants s3:GetObject to Principal '*'.",
            "resource": bucket_aws,
            "region": "us-east-1",
            "raw": asff("Software and Configuration Checks/AWS Security Best Practices",
                        "S3.2 S3 buckets should prohibit public read access", "CRITICAL",
                        "AwsS3Bucket", bucket_aws, "us-east-1"),
        },
        {
            "provider": "azure",
            "source": "Defender for Cloud",
            "category": "misconfiguration",
            "severity": "medium",
            "title": "Storage account allows public blob access",
            "description": "acmelogsprod has allowBlobPublicAccess enabled.",
            "resource": storage_az,
            "region": "eastus",
            "raw": defender("Storage.PublicAccess", "Storage account should prevent public blob access",
                            "Medium", "acmelogsprod"),
        },
    ]


SCENARIOS = {"ddos": ddos, "brute-force": brute_force, "misconfig": misconfig}


# Transport -------------------------------------------------------------------

def post(api: str, path: str, body: dict | None) -> dict | None:
    data = json.dumps(body).encode() if body is not None else b""
    req = request.Request(f"{api}{path}", data=data, method="POST",
                          headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=10) as res:
        payload = res.read()
    return json.loads(payload) if payload else None


def run(api: str, names: list[str], delay: float) -> None:
    for name in names:
        events = SCENARIOS[name]()
        print(f"[{name}] sending {len(events)} events")
        for event in events:
            result = post(api, "/api/events", {"channel": "injection", "events": [event]})
            flags = []
            if result["incidents_created"]:
                flags.append("new incident")
            if result["incidents_updated"]:
                flags.append("incident updated")
            print(f"  {event['provider']:<5} {event['severity']:<8} {event['title']}"
                  + (f"  -> {', '.join(flags)}" if flags else ""))
            time.sleep(delay)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenario", choices=[*SCENARIOS, "all", "reset"])
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--delay", type=float, default=0.4)
    args = parser.parse_args()

    try:
        if args.scenario == "reset":
            post(args.api, "/api/admin/reset", None)
            print("All events and incidents cleared.")
        else:
            names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
            run(args.api, names, args.delay)
    except error.URLError as exc:
        print(f"Cannot reach the backend at {args.api}: {exc.reason}. Is uvicorn running?", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
