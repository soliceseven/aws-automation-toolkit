#!/usr/bin/env python3
"""
CodePipeline Trigger — start an execution and tail stage status.

Usage:
    python codepipeline_trigger.py --pipeline my-pipeline [--profile NAME]
"""

import argparse
import boto3
import sys
import time


def main():
    p = argparse.ArgumentParser(description="Trigger a CodePipeline execution")
    p.add_argument("--pipeline", required=True)
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--wait", action="store_true", help="Wait for completion")
    args = p.parse_args()

    cp = boto3.Session(profile_name=args.profile, region_name=args.region).client("codepipeline")

    exec_id = cp.start_pipeline_execution(name=args.pipeline)["pipelineExecutionId"]
    print(f"Started execution {exec_id} on {args.pipeline}")

    if not args.wait:
        return

    while True:
        time.sleep(20)
        state = cp.get_pipeline_state(name=args.pipeline)
        stages = {s["stageName"]: s["latestExecution"]["status"]
                  for s in state["stageStates"] if "latestExecution" in s}
        line = " | ".join(f"{k}={v}" for k, v in stages.items())
        print(f"  {line}")
        if all(v in ("Succeeded",) for v in stages.values()):
            print("Pipeline SUCCEEDED")
            return
        if any(v in ("Failed", "Stopped", "Superseded") for v in stages.values()):
            print("Pipeline did not succeed", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
