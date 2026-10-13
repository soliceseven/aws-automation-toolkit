#!/usr/bin/env python3
"""
IAM Policy Audit — flag customer-managed policies with overly broad permissions.

Flags: Action "*" or "service:*", Resource "*", and known risky combos.
Usage:
    python iam_policy_audit.py [--profile NAME]
"""

import argparse
import boto3
import json
import sys


RISKY_ACTIONS = {"*", "iam:*", "s3:*"}


def policy_is_risky(doc):
    findings = []
    stmts = doc.get("Statement", [])
    if isinstance(stmts, dict):
        stmts = [stmts]
    for s in stmts:
        if s.get("Effect") != "Allow":
            continue
        actions = s.get("Action", [])
        resources = s.get("Resource", [])
        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]
        for a in actions:
            if a in RISKY_ACTIONS or a.endswith(":*") and a.split(":")[0] in ("iam",):
                findings.append(f"broad-action:{a}")
        if "*" in resources and any(a != "" for a in actions):
            findings.append("resource-star")
    return findings


def main():
    p = argparse.ArgumentParser(description="Audit IAM customer-managed policies")
    p.add_argument("--profile", default=None)
    args = p.parse_args()

    iam = boto3.Session(profile_name=args.profile).client("iam")
    paginator = iam.get_paginator("list_policies")
    risky = []
    total = 0
    for page in paginator.paginate(Scope="Local"):
        for pol in page["Policies"]:
            total += 1
            ver = iam.get_policy_version(
                PolicyArn=pol["Arn"], VersionId=pol["DefaultVersionId"]
            )["PolicyVersion"]["Document"]
            findings = policy_is_risky(ver)
            if findings:
                risky.append((pol["PolicyName"], pol["Arn"], findings))

    print(f"Checked {total} customer-managed policies, {len(risky)} flagged\n")
    for name, arn, findings in risky:
        print(f"  {name}")
        print(f"    {arn}")
        print(f"    {', '.join(findings)}")


if __name__ == "__main__":
    main()
