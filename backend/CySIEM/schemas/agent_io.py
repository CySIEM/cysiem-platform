"""
Structured I/O contracts for the 4-agent pipeline.

The critical design point: Agent 1 (tool-output analyzer) and Agent 2
(raw-log analyzer) MUST emit the same shape, keyed on source_host +
time_window. That is what lets Agent 3 actually join and compare their
findings instead of trying to reconcile free-text opinions. Every field
here is required, not optional, and enforced via Claude's structured
JSON output (see agents/base.py) - not hoped for via prompt wording alone.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    INSUFFICIENT_DATA = "insufficient_data"


class AgentFinding(BaseModel):
    """Common output shape for Agent 1 and Agent 2. Same schema for both
    so Agent 3 can directly compare/join them."""
    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str                              # "agent1_tool_analyzer" | "agent2_log_analyzer"
    source_host: str                              # JOIN KEY
    source_segment: str                           # JOIN KEY (secondary)
    window_start: datetime
    window_end: datetime
    verdict: Verdict
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    evidence_event_ids: List[str] = Field(default_factory=list)   # pointers into OpenSearch
    mitre_techniques: List[str] = Field(default_factory=list)     # e.g. ["T1110", "T1078"]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConsensusResult(BaseModel):
    """Agent 3's output after joining Agent 1 + Agent 2 findings on source_host."""
    consensus_id: str = Field(default_factory=lambda: str(uuid4()))
    source_host: str
    source_segment: str
    agent1_finding: Optional[AgentFinding] = None
    agent2_finding: Optional[AgentFinding] = None
    agreement: bool                                # did both agents land on suspicious/malicious?
    combined_confidence: float = Field(..., ge=0.0, le=1.0)
    escalate_to_verification: bool
    rationale: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationResult(BaseModel):
    """Agent 4's output after querying the Evidence Lake (OpenSearch) for
    historical context on source_host."""
    verification_id: str = Field(default_factory=lambda: str(uuid4()))
    source_host: str
    confirmed: bool
    historical_baseline_deviation: Optional[str] = None
    supporting_event_ids: List[str] = Field(default_factory=list)
    reasoning: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FinalAlert(BaseModel):
    """What Agent 3 pushes to the SOC after Agent 4 confirms."""
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    source_host: str
    source_segment: str
    severity: str                                  # low | medium | high | critical
    title: str
    summary: str
    agent1_summary: str
    agent2_summary: str
    verification_summary: str
    mitre_techniques: List[str] = Field(default_factory=list)
    evidence_event_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanVerdictLabel(str, Enum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    BENIGN_CONFIRMED = "benign_confirmed"   # analyst confirms a dismissed/non-escalated case was indeed benign
    ESCALATED = "escalated"                 # analyst manually escalated something the pipeline missed


class HumanVerdict(BaseModel):
    """
    Captures an analyst's judgment on a FinalAlert (or on a case they
    manually reviewed). This is the v4.1 Layer 9 (Human Review) -> Layer 11
    (Learning Fabric) bridge: published now even though nothing consumes it
    yet, so building the Learning Fabric later means training on real
    historical data from day one, not starting from an empty dataset.
    """
    verdict_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_id: Optional[str] = None          # links back to FinalAlert.alert_id, if applicable
    source_host: str
    label: HumanVerdictLabel
    analyst: str                            # who made the call
    notes: Optional[str] = None
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
