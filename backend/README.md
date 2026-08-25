# KKSIEM v1

AI-assisted SIEM: dual-path detection (tool-based + AI-native) feeding a
4-agent consensus/verification pipeline, built for the pfSense-segmented
lab (LAN + OPT1-4).

This is v1 of a planned roadmap up to **KKSIEM v4.1** (Evidence Lake →
Data Fabric → Canonical Schema → Asset Intelligence → Feature
Store/Security Graph → Detection/Correlation/Investigation Fabrics → AI
Agent Layer → Knowledge Fabric → Security Copilot → Human Review → SOAR →
Learning Fabric). v1 implements Layers 0, 1, 2, 2A, 4, 5, 6, and a 4-agent
version of Layer 7 for real; Layers 3A, 3B, 7A, 8, 10, 11 are explicit,
documented stubs (see the status table below and `roadmap_stubs.py`) - not
silently missing, and not faked.

## v1 → v4.1 migration notes

Four decisions were made specifically so v1 doesn't need to be rewritten
when later layers are added:

1. **Schema versioning + forward-compatible `extensions` field**
   (`kksiem/schemas/canonical.py`). Every `CanonicalEvent` carries
   `schema_version` and an `extensions: dict` field. Layer 2A (Asset
   Intelligence) already writes into `extensions["asset"]` - proving the
   pattern works, not just describing it. v1 consumers that don't check
   `extensions` keep working unmodified because unknown keys inside it are
   just data. `assert_supported_version()` lets any consumer refuse (and
   DLQ) an event whose schema it doesn't recognize.

2. **Externalized correlation state** (`kksiem/agents/correlation_store.py`).
   Agent 3's join logic (matching Agent 1 + Agent 2 findings on
   `source_host`) stores its in-flight state in Redis, not process memory.
   An in-memory dict would silently lose any in-flight correlation on a
   crash or restart, with no error surfaced. Redis-backed state also means
   Agent 3 can be run as multiple replicas later without two replicas
   holding incompatible halves of the same correlation.

3. **Human verdict feedback topic** (`human.verdicts`, `POST /verdicts`).
   Nothing consumes this yet - Layer 11 (Learning Fabric) doesn't exist in
   v1 - but analyst true/false-positive verdicts are captured from day one.

4. **S3-API object storage for the cold tier** (`storage/object_store_client.py`).
   Built on boto3 against local MinIO. Moving to real cloud storage later
   is an `.env` change, not a code change - see "Cloud portability" below.



## v4.1 layer implementation status

| Layer | Status | Module |
|---|---|---|
| L0 Evidence Lake (hot) | Implemented | `storage/opensearch_client.py` |
| L0 Evidence Lake (cold) | Implemented | `storage/object_store_client.py` (MinIO local, S3-compatible) |
| L1 Data Fabric | Implemented | Kafka + Fluent Bit + Winlogbeat |
| L2 Canonical Schema | Implemented, versioned | `schemas/canonical.py` |
| L2A Asset Intelligence | Implemented (basic) | `intelligence/asset_registry.py` |
| L3A Feature Store | Not implemented | stub in `roadmap_stubs.py` |
| L3B Security Graph | Not implemented (partial substitute) | `investigation/investigation_fabric.py::find_related_hosts()` |
| L4 Detection Fabric | Implemented (Suricata + Sigma) | `detection/suricata_bridge.py`, `detection/sigma_runner.py` |
| L5 Correlation Fabric | Implemented | `agents/correlation_store.py` (Redis-backed) |
| L6 Investigation Fabric | Implemented (basic) | `investigation/investigation_fabric.py` |
| L7 AI Agent Layer | Implemented (4-agent) | `agents/agent1-4_*.py` |
| L7A Knowledge Fabric | Not implemented | stub in `roadmap_stubs.py` |
| L8 Security Copilot | Not implemented (REST substitute) | `api/main.py` |
| L9 Human Review | Implemented (basic) | `POST /verdicts`, Slack alerting |
| L10 SOAR | Not implemented | stub in `roadmap_stubs.py` |
| L11 Learning Fabric | Not implemented (data captured) | `human.verdicts` topic |

See `kksiem/roadmap_stubs.py` for exactly what's not built and what v1
substitutes for it in the meantime - each stub raises `NotYetImplemented`
with specifics, rather than silently returning empty data.

## API endpoints

```
GET    /health                     liveness + Redis/OpenSearch dependency check
GET    /events/{host}              raw event history for a host
GET    /alerts                     (placeholder, see topic alerts.confirmed)
POST   /verdicts                   analyst submits true/false-positive verdict
PUT    /assets/{host}               register/update asset criticality, owner, type
GET    /assets/{host}               get one asset's context
GET    /assets                      list all registered assets
DELETE /assets/{host}               remove an asset
GET    /investigate/{host}          Layer 6: full timeline + asset context + stats
GET    /investigate/{host}/related  hosts/IPs that co-occurred in this host's traffic
```

Register your lab hosts once things are running, so Agent 4's verification
weighs criticality correctly:
```bash
curl -X PUT localhost:8000/assets/WIN-SRV01 -H "Content-Type: application/json" -d '{
  "host": "WIN-SRV01", "criticality": "critical",
  "owner": "IT-team", "asset_type": "domain_controller", "segment": "OPT2"
}'
```

## Cloud portability (local now, cloud later)

Object storage (`storage/object_store_client.py`) is written against the
plain S3 API via boto3, pointed at local MinIO by default. Moving to real
cloud storage later means changing `.env` values only:
```bash
OBJECT_STORE_ENDPOINT_URL=          # blank = real AWS S3 auto-resolves
OBJECT_STORE_ACCESS_KEY=<real-key>
OBJECT_STORE_SECRET_KEY=<real-secret>
OBJECT_STORE_REGION=<real-region>
```
No code changes - `tests/test_object_store.py` proves this by running the
exact same client code against a mocked real-AWS-S3 endpoint (no custom
`endpoint_url`) and confirming archive/fetch/list all work identically.

**Note on MinIO specifically**: the official `minio/minio` image repository
was archived by its maintainer in April 2026. `docker-compose.yml` pins the
last verified real release tag. Because the object store client speaks
plain S3 API (not a MinIO-specific SDK), switching to a maintained fork
(e.g. `pgsty/minio`) or any other S3-compatible server is a one-line image
change, not a code change.

### Gaps to close before any real enterprise/production use
These are orthogonal to the v4.1 layer roadmap and apply regardless of
which version you're running:
- **No auth or encryption in transit anywhere** - OpenSearch security
  plugin disabled, Kafka PLAINTEXT listeners, HTTP (not HTTPS) API. Fine
  for an isolated home lab; a hard blocker for real deployment.
- **Single-node everything** - `discovery.type=single-node` on OpenSearch,
  Kafka `replication_factor=1`, single Redis instance, single MinIO node.
  No fault tolerance. A deliberate lab simplification, not an oversight -
  flagging so it isn't mistaken for production-readiness later.
- **No secrets management** - `.env` file with plaintext API keys. An
  enterprise deployment would use Vault, AWS Secrets Manager, or similar.

## How host identity survives the whole pipeline

Every raw log gets wrapped in a **canonical envelope** (`kksiem/schemas/canonical.py`)
at normalization time — `source.host`, `source.segment`, `source.ip` are
required fields on every event, not inferred later from Kafka topic name.
Agent 1 and Agent 2 both emit `AgentFinding` objects that require
`source_host` (`kksiem/schemas/agent_io.py`), enforced via structured JSON
output validation (`kksiem/agents/base.py`) — not just prompted for. That's
what lets Agent 3 join Agent 1's and Agent 2's independent findings on the
same host without ambiguity, and lets Agent 4 query the Evidence Lake
(OpenSearch) filtered to exactly that host's history.

## Pipeline

```
pfSense syslog ──┐
Winlogbeat (Win)  ├─► Kafka raw.* topics ─► Normalizer ─► normalized.events ─► Agent 2 (Path B)
Fluent Bit (Linux)┘                              │
                                                  └─► OpenSearch (Evidence Lake)
Suricata/Wazuh/Sigma ─► tool.alerts ─► Agent 1 (Path A)

Agent 1 findings ──┐
                    ├─► Agent 3 (Consensus, joins on source_host) ─► escalate? ─► Agent 4 (verify vs Evidence Lake)
Agent 2 findings ──┘                                                                    │
                                                                          confirmed? ─► Alert (Slack/log)
```

## File structure

```
kksiem-project/
├── run.py                          # single entrypoint: python run.py <service>
├── docker-compose.yml              # Kafka, OpenSearch, Redis, MinIO, Fluent Bit, all Python services
├── requirements.txt
├── .env.example                    # copy to .env and fill in
├── docker/Dockerfile
├── kksiem/
│   ├── common/
│   │   ├── config.py                # all settings, env-driven
│   │   ├── kafka_client.py          # producer/consumer wrappers w/ retry + DLQ
│   │   └── setup.py                 # creates Kafka topics + OpenSearch template + MinIO bucket
│   ├── schemas/
│   │   ├── canonical.py             # CanonicalEvent - the Layer 2 contract, versioned
│   │   └── agent_io.py              # AgentFinding / ConsensusResult / FinalAlert / HumanVerdict
│   ├── normalizer/
│   │   ├── parsers.py               # per-source-type raw log parsers
│   │   └── service.py               # raw.* -> normalized.events + OpenSearch + MinIO + asset enrichment
│   ├── storage/
│   │   ├── opensearch_client.py     # Evidence Lake hot tier (used by Agent 4, Investigation Fabric)
│   │   └── object_store_client.py   # Evidence Lake cold tier, S3 API (MinIO local, cloud-portable)
│   ├── intelligence/
│   │   └── asset_registry.py        # Layer 2A: host criticality/ownership registry
│   ├── investigation/
│   │   └── investigation_fabric.py  # Layer 6: host timeline + related-hosts queries
│   ├── detection/
│   │   ├── suricata_bridge.py       # tails eve.json -> tool.alerts topic
│   │   ├── sigma_runner.py          # Layer 4: polls OpenSearch against Sigma-style rules
│   │   └── sigma_rules/*.yml        # rule definitions
│   ├── agents/
│   │   ├── base.py                  # Claude structured-JSON call w/ validation retry
│   │   ├── agent1_tool_analyzer.py  # Path A
│   │   ├── agent2_log_analyzer.py   # Path B
│   │   ├── agent3_consensus.py      # Layer 5: joins Agent1+Agent2 on source_host (Redis-backed)
│   │   ├── agent4_verification.py   # queries Evidence Lake + asset context, called by Agent3
│   │   ├── correlation_store.py     # Redis-backed join state for Agent 3
│   │   └── alerting.py              # Slack webhook delivery
│   ├── api/main.py                  # FastAPI: events, assets, investigate, verdicts endpoints
│   ├── roadmap_stubs.py             # explicit NotYetImplemented stubs for L3A/3B/7A/8/10/11
│   └── collectors/configs/          # Fluent Bit + Winlogbeat configs for your lab hosts
└── tests/                           # 29 tests across schema, parsers, correlation, assets, object store, stubs
```

## Run it

### 1. Backbone + all services via Docker Compose (recommended)

```bash
cp .env.example .env
# edit .env: set ANTHROPIC_API_KEY, and KAFKA_BROKERS to this host's OPT4 IP

docker compose up -d --build
docker compose exec normalizer python run.py setup   # create topics + index template + MinIO bucket
```

Check it's alive:
```bash
curl localhost:9200/_cluster/health?pretty     # OpenSearch
curl localhost:8000/health                     # KKSIEM API (also checks Redis + OpenSearch)
open http://localhost:5601                     # OpenSearch Dashboards
open http://localhost:9001                     # MinIO web console
```

### 2. Or run services individually on bare metal (dev/debug)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# start backbone only, via compose:
docker compose up -d zookeeper kafka opensearch opensearch-dashboards redis minio

python run.py setup          # one-time: create topics + index template + MinIO bucket
python run.py normalizer     # terminal 1
python run.py agent1         # terminal 2
python run.py agent2         # terminal 3
python run.py agent3         # terminal 4 (also runs Agent 4 in-process)
python run.py sigma          # terminal 5 (Layer 4 Sigma rule polling)
python run.py api            # terminal 6
```

### 3. Tests

```bash
pip install pytest moto[s3]
redis-server --daemonize yes          # needed for correlation/asset registry tests
pytest tests/ -v                       # 29 tests: schema, parsers, correlation, assets, object store, stubs
```
Tests that need Redis skip gracefully (not fail) if it's unreachable.
Object store tests use `moto` to mock the S3 API directly - no MinIO
required to run them, and they specifically prove the cloud-portability
claim by testing against a mocked real-AWS-S3 shape, not a MinIO-specific one.

## Wiring your lab hosts as collectors

- **pfSense**: Status → System Logs → Settings → enable remote syslog,
  point at your KKSIEM (OPT4) host, port `5140/udp`. The `fluent-bit-pfsense`
  container is already listening (see `docker-compose.yml`).
- **Ubuntu Server (OPT2)**: install Fluent Bit, use
  `kksiem/collectors/configs/fluent-bit-linux.conf`, set `HOST_NAME`,
  `HOST_IP`, `KAFKA_BROKERS` env vars before starting.
- **Windows Server / 10 / 11**: install Winlogbeat, use
  `kksiem/collectors/configs/winlogbeat.yml`, edit the `fields:` block per
  machine (host, ip, segment, source_type) before install.
- **Suricata** (wherever you deploy it): run
  `kksiem/detection/suricata_bridge.py` alongside it with `HOST_NAME`,
  `HOST_SEGMENT`, `SURICATA_EVE_PATH` env vars set.
- **Sigma rules**: drop `.yml` rule files into
  `kksiem/detection/sigma_rules/` (two starters included), run
  `python run.py sigma`. Rules poll OpenSearch every 60s, so they need the
  normalizer already writing events there.

## Error handling notes

- Kafka consumer commits offsets only after successful processing; failures
  are logged and pushed to `dlq.normalizer` rather than crashing the loop
  or silently dropping the message.
- Agent Claude calls validate output against the Pydantic schema and retry
  once with the validation error fed back before giving up.
- Parsers never throw on malformed input — each has a safe fallback that
  still produces a valid `NormalizedFields` with the raw message preserved.
- Unregistered hosts (Layer 2A) degrade to `criticality=unknown` rather
  than erroring - asset registration is expected to lag behind new hosts
  appearing in logs.
- Cold-tier (MinIO/S3) archive failures are logged but non-fatal - they
  don't block the hot-tier (OpenSearch) write or Path B forwarding, since
  cold storage serves later forensics, not the real-time detection path.
- Agent 3 refuses to start if Redis is unreachable (fails loudly at
  startup) rather than silently running with no durable correlation state.

## Extending

- Add a new source type: write a parser in `normalizer/parsers.py`, add to
  `PARSER_DISPATCH`, add a `SourceType` enum value in `schemas/canonical.py`.
- Add a new detection tool: write a bridge script like `suricata_bridge.py`
  that publishes to `tool.alerts` in the same shape, or add Sigma-style
  rules to `detection/sigma_rules/`.
- Add a new alert channel: extend `agents/alerting.py`.
- Add a new `extensions` field (e.g. for a future Layer 3B graph node ID):
  write it in the normalizer, read it wherever needed - no schema
  migration required, see "How host identity survives the whole pipeline"
  above.
- Build out a stubbed v4.1 layer: replace the relevant function in
  `roadmap_stubs.py`, update the status table above.
