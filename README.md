# AWS Automation Toolkit

Python/Boto3 scripts for building and automating pipelines on AWS — Lambda deployments, ECR pushes, CloudFormation deploys, CodePipeline triggers, and IAM audits.

## Scripts

| Script | What it does |
|--------|--------------|
| `lambda_deploy.py` | Zips a Lambda function dir and publishes a new version |
| `ecr_push.py` | Builds a Docker image and pushes it to ECR |
| `cfn_deploy.py` | Deploys/updates a CloudFormation stack from a template |
| `codepipeline_trigger.py` | Starts a CodePipeline execution and tails its status |
| `s3_sync.py` | Syncs a local dir to S3 (artifacts, static sites) |
| `iam_policy_audit.py` | Flags overly permissive IAM policies (`*` actions/resources) |

## Setup

```bash
pip install boto3
aws configure
```

Docker required for `ecr_push.py`.

## Pipeline thinking

These are the glue scripts between "code is written" and "code is running" — the unglamorous automation that makes deployments boring (in the best way).
