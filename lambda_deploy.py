#!/usr/bin/env python3
"""
Package a function directory and update a Lambda function. Use `--publish` to publish a new version.

Usage:
    python lambda_deploy.py --function my-func --src ./lambda_src [--profile NAME]
"""

import argparse
import io
import sys
import zipfile
from pathlib import Path

import boto3


def zip_dir(src: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in src.rglob("*"):
            if f.is_file() and "__pycache__" not in str(f):
                z.write(f, f.relative_to(src))
    buf.seek(0)
    return buf.read()


def main():
    p = argparse.ArgumentParser(description="Package and deploy a Lambda function")
    p.add_argument("--function", required=True, help="Lambda function name")
    p.add_argument("--src", required=True, help="Source directory to zip")
    p.add_argument("--profile", default=None)
    p.add_argument("--publish", action="store_true", help="Publish a new version")
    args = p.parse_args()

    src = Path(args.src)
    if not src.is_dir():
        print(f"Not a directory: {src}", file=sys.stderr)
        sys.exit(1)

    payload = zip_dir(src)
    print(f"Packaged {src} -> {len(payload) / 1024:.1f} KB")

    lam = boto3.Session(profile_name=args.profile).client("lambda")
    resp = lam.update_function_code(FunctionName=args.function, ZipFile=payload)
    print(f"Updated {args.function} (last modified {resp['LastModified']})")

    if args.publish:
        ver = lam.publish_version(FunctionName=args.function)
        print(f"Published version {ver['Version']}")


if __name__ == "__main__":
    main()
