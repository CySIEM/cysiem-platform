"""
Correlation state store (Layer 5 concern, used by Agent 3).

v1's first implementation held Agent 3's "waiting for the other agent's
finding on this host" state in a plain Python dict inside the process. That
breaks in two ways that matter for an enterprise deployment:
  1. A crash or restart silently drops any host currently mid-correlation -
     no error, no trace, the escalation just never happens.
  2. It can't be horizontally scaled - two Agent 3 replicas would each hold
     their own half of the picture and might never see both findings.

This module replaces that dict with Redis. Any number of Agent 3 replicas
can share this store safely, and a restart loses nothing (state lives in
Redis, not process memory). If Redis is unreachable, calls raise rather
than silently losing state - the caller decides how to handle that (retry,
crash-and-restart, route to DLQ), but it is never silently swallowed.
"""
from __future__ import annotations
import json
import logging
import time
from typing import Optional
import redis
from CySIEM.common.config import settings
from CySIEM.schemas.agent_io import AgentFinding

logger = logging.getLogger("kksiem.correlation_store")

KEY_PREFIX = "kksiem:correlation:"


class CorrelationStore:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    def _key(self, host: str) -> str:
        return f"{KEY_PREFIX}{host}"

    def record_finding(self, host: str, slot: str, finding: AgentFinding):
        """
        Records a finding for (host, slot). Returns (f1, f2, claimed_by_me):
          - f1, f2: current AgentFinding for each slot (None if not yet seen)
          - claimed_by_me: True if THIS call completed the pair (both slots
            now filled) and is responsible for evaluating it. Uses an atomic
            GETDEL-after-set pattern so two near-simultaneous writers (agent1
            and agent2 findings landing within milliseconds of each other)
            can't both think they own evaluation.
        """
        key = self._key(host)
        now = time.time()

        with self.redis.pipeline() as pipe:
            for _ in range(5):  # bounded retry on optimistic-lock contention
                try:
                    pipe.watch(key)
                    raw = pipe.get(key)
                    entry = json.loads(raw) if raw else {"agent1": None, "agent2": None, "first_seen": now}
                    entry[slot] = finding.model_dump(mode="json")
                    is_complete = entry["agent1"] is not None and entry["agent2"] is not None

                    pipe.multi()
                    if is_complete:
                        pipe.delete(key)  # claim it - remove so nobody else double-processes
                    else:
                        pipe.set(key, json.dumps(entry), ex=self.ttl_seconds)
                    pipe.execute()
                    break
                except redis.WatchError:
                    continue
            else:
                raise RuntimeError(f"Failed to update correlation state for host={host} after retries")

        f1 = AgentFinding(**entry["agent1"]) if entry["agent1"] else None
        f2 = AgentFinding(**entry["agent2"]) if entry["agent2"] else None
        return f1, f2, is_complete

    def sweep_expired(self, min_age_seconds: int) -> list[tuple[str, Optional[AgentFinding], Optional[AgentFinding]]]:
        """
        Finds correlation entries older than min_age_seconds that never got
        a second finding, claims them (atomic GETDEL so concurrent sweepers
        or a simultaneous record_finding() call can't double-process), and
        returns them for solo evaluation instead of leaving them to expire
        unnoticed via TTL alone.
        """
        results = []
        cursor = 0
        now = time.time()
        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match=f"{KEY_PREFIX}*", count=100)
            for key in keys:
                raw = self.redis.get(key)
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if now - entry.get("first_seen", now) >= min_age_seconds:
                    deleted = self.redis.getdel(key)
                    if not deleted:
                        continue  # already claimed by another sweeper/writer
                    entry = json.loads(deleted)
                    host = key[len(KEY_PREFIX):]
                    f1 = AgentFinding(**entry["agent1"]) if entry.get("agent1") else None
                    f2 = AgentFinding(**entry["agent2"]) if entry.get("agent2") else None
                    if f1 or f2:
                        results.append((host, f1, f2))
            if cursor == 0:
                break
        return results

    def health_check(self) -> bool:
        try:
            return bool(self.redis.ping())
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
