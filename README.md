# AWS Automation Toolkit

Use these Python and Boto3 scripts to automate AWS workflows: deploy Lambda functions, push images to ECR, deploy CloudFormation stacks, trigger CodePipeline executions, sync files to S3, and audit IAM policies. They are for engineers who deploy to AWS regularly and want each step as one repeatable command.

## Overview

Each script is standalone: no framework, no configuration file, no shared state. Pick one and run it from the command line with an AWS profile. They use the default AWS credential chain when `--profile` is omitted.

## Scripts

| Script | What it does |
|--------|--------------|
| `lambda_deploy.py` | Packages a Lambda function from a source directory, updates it, and optionally publishes a version with `--publish` |
| `ecr_push.py` | Builds a Docker image and pushes it to ECR |
| `cfn_deploy.py` | Creates or updates a CloudFormation stack from a template, with `Key=Val` parameter overrides |
| `codepipeline_trigger.py` | Starts a CodePipeline execution and optionally waits for its status with `--wait` |
| `s3_sync.py` | Syncs a local directory to S3, such as build artifacts or static site files, and optionally deletes remote objects that are no longer present locally |
| `iam_policy_audit.py` | Audits customer-managed policies for `Allow` statements with `*` or service-wide wildcard actions (for example, `s3:*` or `iam:*`), or `Resource: *` |

## Installation

### Prerequisites

- Python 3
- `boto3`
- AWS credentials configured, via `aws configure` or an IAM role
- Docker, for `ecr_push.py` only

### Quick Install

```bash
git clone https://github.com/soliceseven/aws-automation-toolkit.git
cd aws-automation-toolkit
pip install boto3
```

### Verification

```bash
python3 lambda_deploy.py --help
# Expected output:
# usage: lambda_deploy.py [-h] --function FUNCTION --src SRC [--profile PROFILE]
#                         [--publish]
```

## Quick Start

```bash
# Zip ./lambda, update the function, and publish a new version
python3 lambda_deploy.py --function my-function --src ./lambda --profile my-aws-profile --publish
```

## Usage

### Common flags

- `--profile NAME`: AWS CLI profile to use (all scripts; omit to use the default credential chain). If the profile is invalid or credentials are missing, the script exits with a clear message instead of a raw stack trace.
- `--region REGION`: AWS region (`ecr_push.py`, `cfn_deploy.py`, `codepipeline_trigger.py`). Omit to use the profile's default region.

Run any script with `--help` for its full flag list.

### Examples

```bash
# Build the image in ./app and push it to ECR as my-app:v1.2.3
python3 ecr_push.py --repo my-app --tag v1.2.3 --context ./app --profile my-aws-profile

# Create or update a stack from a template, with parameter overrides
python3 cfn_deploy.py --stack my-stack --template template.yaml \
  --params Environment=prod InstanceType=t3.large --profile my-aws-profile

# Start a pipeline execution and wait for it to finish
python3 codepipeline_trigger.py --pipeline my-pipeline --wait --profile my-aws-profile

# Sync build output to S3 under a prefix; --delete removes remote objects
# that are no longer present locally, so leave it off unless you mean it
python3 s3_sync.py --src ./dist --bucket my-bucket --prefix releases/v1 --profile my-aws-profile

# Audit customer-managed IAM policies for wildcard actions and resources
python3 iam_policy_audit.py --profile my-aws-profile
```

## Testing

```bash
python3 -m unittest discover -s tests
```

The test suite uses `unittest` with boto3 stubbed out, so it runs without real credentials or network access.

## Why this exists

These scripts automate the steps between writing code and running it, so deployments follow a repeatable process instead of console clicks.
