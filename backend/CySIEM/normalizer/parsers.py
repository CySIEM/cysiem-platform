"""
Source-specific parsers. Each takes a raw log string and returns a
NormalizedFields object. These are intentionally simple / regex-based —
good enough to extract the fields your agents actually need
(user, action, src/dest IP, outcome) without pulling in a heavy parsing
dependency. Extend the regexes as you encounter real log samples from
your lab; treat this file as living documentation of your actual formats.
"""
from __future__ import annotations
import re
import json
import logging
from CySIEM.schemas.canonical import NormalizedFields, EventCategory

logger = logging.getLogger("kksiem.normalizer.parsers")


def parse_pfsense_filterlog(raw: str) -> NormalizedFields:
    """
    pfSense filterlog (CSV-ish) format, roughly:
    <timestamp> filterlog[...]: 5,,,1000000103,em2,match,pass,in,4,...,proto,src,dst,srcport,dstport,...
    We split on the filterlog payload and pull the fields we care about.
    """
    try:
        payload = raw.split("filterlog[")[-1]
        payload = payload.split(":", 1)[-1].strip()
        parts = payload.split(",")
        # Defensive indexing - pfSense filterlog format has ~20+ CSV fields,
        # exact index of proto/src/dst shifts by IP version. Handle common case.
        action = "pass" if "pass" in payload else ("block" if "block" in payload else None)
        src_ip = None
        dest_ip = None
        proto = None
        # crude but effective: pfSense puts src/dest as dotted-quad fields late in the line
        ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        ips = ip_pattern.findall(payload)
        if len(ips) >= 2:
            src_ip, dest_ip = ips[0], ips[1]
        for proto_name in ("TCP", "UDP", "ICMP"):
            if proto_name in payload.upper():
                proto = proto_name
                break

        return NormalizedFields(
            event_category=EventCategory.FIREWALL_TRAFFIC,
            action=f"conn_{action}" if action else "conn_unknown",
            src_ip=src_ip,
            dest_ip=dest_ip,
            protocol=proto,
            outcome="success" if action == "pass" else "blocked",
            message=raw[:200],
        )
    except Exception as e:
        logger.warning(f"pfSense parse fallback: {e}")
        return NormalizedFields(event_category=EventCategory.OTHER, message=raw[:200])


def parse_windows_eventlog(raw: str) -> NormalizedFields:
    """
    Winlogbeat ships JSON. Expect `raw` to be a JSON string containing
    at least event.code, winlog.event_data.TargetUserName, etc.
    """
    try:
        doc = json.loads(raw)
        event_code = str(doc.get("event", {}).get("code", ""))
        winlog = doc.get("winlog", {}) or {}
        event_data = winlog.get("event_data", {}) or {}

        user = event_data.get("TargetUserName") or event_data.get("SubjectUserName")
        src_ip = event_data.get("IpAddress")
        process_name = event_data.get("NewProcessName") or event_data.get("Image")
        parent_process = event_data.get("ParentProcessName")

        category = EventCategory.OTHER
        action = None
        outcome = None

        # Common security event IDs worth mapping explicitly
        if event_code == "4624":
            category, action, outcome = EventCategory.AUTHENTICATION, "logon_success", "success"
        elif event_code == "4625":
            category, action, outcome = EventCategory.AUTHENTICATION, "logon_failed", "failure"
        elif event_code == "4688":
            category, action = EventCategory.PROCESS, "process_created"
        elif event_code == "4720":
            category, action = EventCategory.SYSTEM, "user_account_created"
        elif event_code == "1":  # Sysmon process creation
            category, action = EventCategory.PROCESS, "process_created"

        return NormalizedFields(
            event_category=category,
            action=action,
            user=user,
            process_name=process_name,
            parent_process=parent_process,
            src_ip=src_ip,
            outcome=outcome,
            message=doc.get("message", raw)[:200],
        )
    except Exception as e:
        logger.warning(f"Windows eventlog parse fallback: {e}")
        return NormalizedFields(event_category=EventCategory.OTHER, message=raw[:200])


def parse_linux_auditd(raw: str) -> NormalizedFields:
    """
    auditd log lines, e.g.:
    type=USER_AUTH msg=audit(...): user pid=1234 uid=0 auid=1000 ... res=failed
    type=SYSCALL msg=audit(...): ... exe="/usr/bin/bash" ...
    """
    try:
        kv = dict(re.findall(r'(\w+)=("[^"]*"|\S+)', raw))
        audit_type = kv.get("type", "")
        outcome = "failure" if "res=failed" in raw or "success=no" in raw else (
            "success" if "res=success" in raw or "success=yes" in raw else None
        )
        exe = kv.get("exe", "").strip('"')
        uid = kv.get("uid") or kv.get("auid")

        category = EventCategory.OTHER
        action = audit_type.lower() if audit_type else None
        if "AUTH" in audit_type or "USER_LOGIN" in audit_type:
            category = EventCategory.AUTHENTICATION
        elif "SYSCALL" in audit_type or "EXECVE" in audit_type:
            category = EventCategory.PROCESS

        return NormalizedFields(
            event_category=category,
            action=action,
            user=uid,
            process_name=exe or None,
            outcome=outcome,
            message=raw[:200],
        )
    except Exception as e:
        logger.warning(f"auditd parse fallback: {e}")
        return NormalizedFields(event_category=EventCategory.OTHER, message=raw[:200])


def parse_linux_syslog(raw: str) -> NormalizedFields:
    """Generic syslog fallback for non-auditd Linux lines (sshd, sudo, etc)."""
    outcome = None
    action = None
    category = EventCategory.OTHER
    user = None

    if "Failed password" in raw:
        category, action, outcome = EventCategory.AUTHENTICATION, "logon_failed", "failure"
        m = re.search(r"for (?:invalid user )?(\S+) from (\S+)", raw)
        if m:
            user = m.group(1)
    elif "Accepted password" in raw or "Accepted publickey" in raw:
        category, action, outcome = EventCategory.AUTHENTICATION, "logon_success", "success"
        m = re.search(r"for (\S+) from (\S+)", raw)
        if m:
            user = m.group(1)
    elif "sudo:" in raw:
        category, action = EventCategory.SYSTEM, "sudo_command"

    src_ip = None
    ip_match = re.search(r"from ((?:\d{1,3}\.){3}\d{1,3})", raw)
    if ip_match:
        src_ip = ip_match.group(1)

    return NormalizedFields(
        event_category=category,
        action=action,
        user=user,
        src_ip=src_ip,
        outcome=outcome,
        message=raw[:200],
    )


# Dispatch table: log_type (as tagged by the collector) -> parser function
PARSER_DISPATCH = {
    "pfsense_filterlog": parse_pfsense_filterlog,
    "security_eventlog": parse_windows_eventlog,
    "sysmon": parse_windows_eventlog,
    "auditd": parse_linux_auditd,
    "syslog": parse_linux_syslog,
}


def parse(log_type: str, raw: str) -> NormalizedFields:
    parser_fn = PARSER_DISPATCH.get(log_type)
    if parser_fn is None:
        logger.debug(f"No parser for log_type={log_type}, storing raw only")
        return NormalizedFields(event_category=EventCategory.OTHER, message=raw[:200])
    return parser_fn(raw)
