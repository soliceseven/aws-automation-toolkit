#!/usr/bin/env python3
"""
ECR Push — build a Docker image and push it to ECR.

Usage:
    python ecr_push.py --repo my-app --tag v1.2 [--dockerfile ./Dockerfile --context .]
Requires: docker CLI logged in (aws ecr get-login-password | docker login ...)
"""

import argparse
import base64
import subprocess
import sys

import boto3


def run(cmd, **kw):
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(r.returncode)


def main():
    p = argparse.ArgumentParser(description="Build and push Docker image to ECR")
    p.add_argument("--repo", required=True, help="ECR repository name")
    p.add_argument("--tag", default="latest")
    p.add_argument("--dockerfile", default="Dockerfile")
    p.add_argument("--context", default=".")
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    args = p.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ecr = session.client("ecr")
    region = session.region_name or "us-east-1"

    try:
        desc = ecr.describe_repositories(repositoryNames=[args.repo])["repositories"][0]
    except ecr.exceptions.RepositoryNotFoundException:
        desc = ecr.create_repository(repositoryName=args.repo)["repository"]
        print(f"Created ECR repo {args.repo}")
    uri = desc["repositoryUri"]

    token = ecr.get_authorization_token()["authorizationData"][0]
    pw = base64.b64decode(token["authorizationToken"]).decode().split(":", 1)[1]
    registry = token["proxyEndpoint"]
    run(
        ["docker", "login", "--username", "AWS", "--password-stdin", registry],
        input=pw.encode(),
    )

    image = f"{uri}:{args.tag}"
    run(["docker", "build", "-f", args.dockerfile, "-t", image, args.context])
    run(["docker", "push", image])
    print(f"Pushed {image}")


if __name__ == "__main__":
    main()
