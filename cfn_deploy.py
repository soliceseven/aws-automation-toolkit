#!/usr/bin/env python3
"""
CloudFormation Deploy — create or update a stack from a template.

Usage:
    python cfn_deploy.py --stack my-stack --template template.yaml [--params Key=Val ...]
"""

import argparse
import boto3
import sys
import time


def wait_for_stack(cfn, stack, timeout=1800):
    start = time.time()
    while time.time() - start < timeout:
        desc = cfn.describe_stacks(StackName=stack)["Stacks"][0]
        status = desc["StackStatus"]
        print(f"  {status}")
        if status.endswith("_COMPLETE"):
            return True
        if status.endswith("_FAILED") or "ROLLBACK" in status:
            print(f"Stack failed: {status}", file=sys.stderr)
            return False
        time.sleep(15)
    print("Timed out waiting for stack", file=sys.stderr)
    return False


def main():
    p = argparse.ArgumentParser(description="Deploy a CloudFormation stack")
    p.add_argument("--stack", required=True)
    p.add_argument("--template", required=True, help="Path to template file")
    p.add_argument("--params", nargs="*", default=[], help="Key=Val overrides")
    p.add_argument("--capabilities", nargs="*", default=["CAPABILITY_IAM"],
                   help="e.g. CAPABILITY_IAM CAPABILITY_NAMED_IAM")
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    args = p.parse_args()

    with open(args.template) as f:
        body = f.read()

    params = []
    for kv in args.params:
        k, _, v = kv.partition("=")
        params.append({"ParameterKey": k, "ParameterValue": v})

    cfn = boto3.Session(profile_name=args.profile, region_name=args.region).client("cloudformation")

    exists = True
    try:
        cfn.describe_stacks(StackName=args.stack)
    except cfn.exceptions.ClientError:
        exists = False

    kwargs = dict(StackName=args.stack, TemplateBody=body,
                  Parameters=params, Capabilities=args.capabilities)
    if exists:
        print(f"Updating stack {args.stack}...")
        try:
            cfn.update_stack(**kwargs)
        except cfn.exceptions.ClientError as e:
            if "No updates are to be performed" in str(e):
                print("No changes.")
                return
            raise
    else:
        print(f"Creating stack {args.stack}...")
        cfn.create_stack(**kwargs)

    ok = wait_for_stack(cfn, args.stack)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
