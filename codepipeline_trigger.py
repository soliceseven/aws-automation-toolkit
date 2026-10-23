#!/usr/bin/env python3
"""
CodePipeline Trigger — start an execution and optionally wait for its status.

Usage:
    python codepipeline_trigger.py --pipeline my-pipeline [--profile NAME]
"""

import argparse
import sys
import time

import boto3


def main():
    p = argparse.ArgumentParser(description="Trigger a CodePipeline execution")
    p.add_argument("--pipeline", required=True)
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--wait", action="store_true", help="Wait for completion")
    args = p.parse_args()

    cp = boto3.Session(profile_name=args.profile, region_name=args.region).client(
        "codepipeline"
    )

    exec_id = cp.start_pipeline_execution(name=args.pipeline)["pipelineExecutionId"]
    print(f"Started execution {exec_id} on {args.pipeline}")

    if not args.wait:
        return

    while True:
        time.sleep(20)
        status = cp.get_pipeline_execution(
            pipelineName=args.pipeline, pipelineExecutionId=exec_id
        )["pipelineExecution"]["status"]
        print(f"  Execution={status}")
        if status == "Succeeded":
            print("Pipeline SUCCEEDED")
            return
        if status in ("Failed", "Stopped", "Superseded", "Cancelled"):
            print("Pipeline did not succeed", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
