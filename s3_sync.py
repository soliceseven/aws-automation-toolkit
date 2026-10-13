#!/usr/bin/env python3
"""
S3 Sync — upload a local directory to S3 (artifacts, static sites).

Usage:
    python s3_sync.py --src ./dist --bucket my-bucket [--prefix artifacts/] [--delete]
"""

import argparse
import boto3
import mimetypes
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="Sync a local directory to S3")
    p.add_argument("--src", required=True)
    p.add_argument("--bucket", required=True)
    p.add_argument("--prefix", default="")
    p.add_argument("--delete", action="store_true",
                   help="Delete remote objects not present locally")
    p.add_argument("--profile", default=None)
    args = p.parse_args()

    src = Path(args.src)
    if not src.is_dir():
        print(f"Not a directory: {src}", file=sys.stderr)
        sys.exit(1)

    s3 = boto3.Session(profile_name=args.profile).client("s3")
    prefix = args.prefix.strip("/") + "/" if args.prefix.strip("/") else ""

    local_keys = set()
    uploaded = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        key = prefix + str(f.relative_to(src)).replace("\\", "/")
        local_keys.add(key)
        ctype, _ = mimetypes.guess_type(str(f))
        extra = {"ContentType": ctype} if ctype else {}
        s3.upload_file(str(f), args.bucket, key, ExtraArgs=extra)
        uploaded += 1
    print(f"Uploaded {uploaded} files to s3://{args.bucket}/{prefix}")

    if args.delete:
        paginator = s3.get_paginator("list_objects_v2")
        removed = 0
        for page in paginator.paginate(Bucket=args.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if obj["Key"] not in local_keys:
                    s3.delete_object(Bucket=args.bucket, Key=obj["Key"])
                    removed += 1
        print(f"Deleted {removed} stale remote objects")


if __name__ == "__main__":
    main()
