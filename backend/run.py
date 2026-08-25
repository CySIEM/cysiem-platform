#!/usr/bin/env python3
"""
Single entrypoint for every KKSIEM service.

Usage:
    python run.py normalizer      # Layer 2 normalizer
    python run.py agent1          # tool-output analyzer (Path A)
    python run.py agent2          # raw-log analyzer (Path B)
    python run.py agent3          # consensus (calls Agent 4 in-process for verification)
    python run.py sigma           # Layer 4 Sigma rule runner
    python run.py api             # FastAPI dashboard/status API
    python run.py setup           # create Kafka topics + OpenSearch template + MinIO bucket

Note: there is no standalone "agent4" service. Agent 4 (verification) is a
library called synchronously by Agent 3 during consensus escalation - see
kksiem/agents/agent4_verification.py's run_verification(), invoked from
agent3_consensus.py. This matches the flow: Agent 3 evaluates consensus,
calls Agent 4 in-process, gets a verdict back, then pushes the alert - all
within Agent 3's process, not a separate Kafka-consuming service.

This exists so you don't need to remember module paths - one command per
service, matching the "npm install && npm start" simplicity you asked for.
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    service = sys.argv[1]

    if service == "normalizer":
        from CySIEM.normalizer.service import NormalizerService
        NormalizerService().run()

    elif service == "agent1":
        from CySIEM.agents.agent1_tool_analyzer import Agent1Service
        Agent1Service().run()

    elif service == "agent2":
        from CySIEM.agents.agent2_log_analyzer import Agent2Service
        Agent2Service().run()

    elif service == "agent3":
        from CySIEM.agents.agent3_consensus import Agent3Service
        Agent3Service().run()

    elif service == "sigma":
        from CySIEM.detection.sigma_runner import SigmaRunner
        SigmaRunner().run()

    elif service == "api":
        import uvicorn
        uvicorn.run("kksiem.api.main:app", host="0.0.0.0", port=8000, reload=False)

    elif service == "setup":
        from CySIEM.common.setup import run_setup
        run_setup()

    else:
        print(f"Unknown service: {service}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
