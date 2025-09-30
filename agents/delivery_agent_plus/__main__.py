"""Module entrypoint for running DeliveryAgentPlus."""
from __future__ import annotations

import argparse
import uvicorn

from .agent import root_agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Delivery Agent Plus server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=10005, help="Port to bind")
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the agent response once instead of starting the server",
    )
    args = parser.parse_args()

    if args.print_only:
        print(root_agent.handle())
        return

    uvicorn.run("agents.delivery_agent_plus.server:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
