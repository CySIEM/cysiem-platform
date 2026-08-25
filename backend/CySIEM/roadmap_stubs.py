"""
v4.1 layers NOT YET IMPLEMENTED in v1.

This module exists so "not built yet" is an explicit, importable,
documented fact rather than silent absence someone discovers by grep-ing
for a module that doesn't exist. Each stub raises NotImplementedError with
a note on what it will do and what v1 substitutes for it in the meantime,
so nobody mistakes "the function exists" for "the feature works".

Layer 3A - Feature Store:
    Will compute and serve reusable behavioral features (e.g. "failed
    logon rate for this host over trailing 7 days") to detection/agents,
    versioned and consistent between training and inference. v1 substitute:
    Agent 2/Agent 4 recompute ad hoc context from raw OpenSearch queries
    each time - works, but nothing is cached, versioned, or reused across
    agents.

Layer 3B - Security Graph:
    Will maintain real entity-relationship graph (host-to-host,
    user-to-host, process lineage) via a graph database (Neo4j per the
    original architecture doc). v1 substitute:
    investigation/investigation_fabric.py's find_related_hosts() does a
    same-window IP co-occurrence scan - not a graph, no traversal, no
    persistence of relationships over time.

Layer 7A - Knowledge Fabric (RAG + Vector DB):
    Will let agents retrieve relevant historical incidents, runbooks, and
    threat intel via semantic search over a vector database. v1 substitute:
    none - Agent 4's "historical baseline" is a literal recent-events query,
    not semantic retrieval over incident knowledge.

Layer 8 - Security Copilot:
    Will provide an interactive chat interface for analysts to query the
    Investigation Fabric, Knowledge Fabric, and Security Graph
    conversationally. v1 substitute: the FastAPI /events, /assets, /alerts
    endpoints (kksiem/api/main.py) provide the same underlying data, but as
    a few fixed REST endpoints, not a conversational agent.

Layer 10 - SOAR (Security Orchestration, Automation and Response):
    Will take automated response actions (isolate host, disable account,
    block IP at firewall) after a confirmed alert, not just notify a human.
    v1 substitute: agents/alerting.py sends a Slack notification only - a
    human takes every response action manually.

Layer 11 - Learning Fabric / Model Registry:
    Will retrain/fine-tune detection thresholds and agent prompts based on
    accumulated human.verdicts data, with versioned model/prompt releases.
    v1 substitute: human.verdicts topic captures the raw data
    (schemas/agent_io.py HumanVerdict, api/main.py POST /verdicts) but
    nothing consumes or trains on it yet - the data is being collected so
    this layer doesn't start from zero later.
"""


class NotYetImplemented(NotImplementedError):
    pass


def feature_store_get(host: str, feature_name: str):
    raise NotYetImplemented(
        "Layer 3A (Feature Store) is not implemented in v1. "
        "See this module's docstring for the v1 substitute."
    )


def security_graph_query(host: str, relationship: str):
    raise NotYetImplemented(
        "Layer 3B (Security Graph) is not implemented in v1. "
        "Use kksiem.investigation.investigation_fabric.find_related_hosts() "
        "for a partial substitute (IP co-occurrence, not a real graph)."
    )


def knowledge_fabric_search(query: str):
    raise NotYetImplemented(
        "Layer 7A (Knowledge Fabric / RAG) is not implemented in v1. "
        "There is no substitute currently - agents do not have access to "
        "historical incident knowledge or runbooks."
    )


def security_copilot_chat(message: str, session_id: str):
    raise NotYetImplemented(
        "Layer 8 (Security Copilot) is not implemented in v1. "
        "Use the REST endpoints in kksiem.api.main directly instead."
    )


def soar_execute_response(action: str, target_host: str, params: dict):
    raise NotYetImplemented(
        "Layer 10 (SOAR) is not implemented in v1. No automated response "
        "actions are taken - kksiem.agents.alerting only notifies a human, "
        "who must act manually."
    )


def learning_fabric_retrain():
    raise NotYetImplemented(
        "Layer 11 (Learning Fabric / Model Registry) is not implemented in "
        "v1. Human verdicts ARE being captured (topic: human.verdicts, see "
        "POST /verdicts) so training data accumulates, but nothing consumes "
        "it yet."
    )
