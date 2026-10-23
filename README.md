# AWS Automation Toolkit

Use these Python and Boto3 scripts to automate AWS workflows: deploy Lambda functions, push images to ECR, deploy CloudFormation stacks, trigger CodePipeline executions, sync files to S3, and audit IAM policies.

## Scripts

| Script | What it does |
|--------|--------------|
| `lambda_deploy.py` | Packages a Lambda function, updates it, and optionally publishes a version with `--publish` |
| `ecr_push.py` | Builds a Docker image and pushes it to ECR |
| `cfn_deploy.py` | Creates or updates a CloudFormation stack from a template |
| `codepipeline_trigger.py` | Starts a CodePipeline execution and optionally waits for its status with `--wait` |
| `s3_sync.py` | Syncs a local directory to S3, such as build artifacts or static site files |
| `iam_policy_audit.py` | Audits customer-managed policies for `Allow` statements with `*` or service-wide wildcard actions (for example, `s3:*` or `iam:*`), or `Resource: *` |

## Setup

```bash
pip install boto3
aws configure
```

Docker required for `ecr_push.py`.

## Pipeline thinking

These scripts automate the steps between writing code and running it, so deployments follow a repeatable process.
