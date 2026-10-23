import importlib
import io
import mimetypes
import sys
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock


_boto3_stub = types.ModuleType("boto3")
with mock.patch.dict(sys.modules, {"boto3": _boto3_stub}):
    cfn_deploy = importlib.import_module("cfn_deploy")
    codepipeline_trigger = importlib.import_module("codepipeline_trigger")
    ecr_push = importlib.import_module("ecr_push")
    iam_policy_audit = importlib.import_module("iam_policy_audit")
    lambda_deploy = importlib.import_module("lambda_deploy")
    s3_sync = importlib.import_module("s3_sync")


class FakeClientError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.response = {"Error": {"Code": code}}


class ToolTests(unittest.TestCase):
    def test_cloudformation_rollback_complete_is_not_success(self):
        client = mock.Mock()
        client.describe_stacks.return_value = {
            "Stacks": [{"StackStatus": "UPDATE_ROLLBACK_COMPLETE"}]
        }

        self.assertFalse(cfn_deploy.wait_for_stack(client, "example"))

    def test_cloudformation_create_complete_is_success(self):
        client = mock.Mock()
        client.describe_stacks.return_value = {
            "Stacks": [{"StackStatus": "CREATE_COMPLETE"}]
        }

        self.assertTrue(cfn_deploy.wait_for_stack(client, "example"))

    def test_cloudformation_only_missing_stack_error_triggers_create(self):
        client = mock.Mock()
        client.exceptions = types.SimpleNamespace(ClientError=FakeClientError)
        client.describe_stacks.side_effect = FakeClientError(
            "Stack with id example does not exist", "ValidationError"
        )
        client.create_stack.return_value = None
        fake_boto3 = types.SimpleNamespace(
            Session=mock.Mock(return_value=types.SimpleNamespace(
                client=mock.Mock(return_value=client)
            ))
        )
        with (
            mock.patch.object(cfn_deploy, "boto3", fake_boto3),
            mock.patch.object(cfn_deploy.sys, "argv", [
                "cfn_deploy.py", "--stack", "example", "--template", "template.yaml"
            ]),
            mock.patch("builtins.open", mock.mock_open(read_data="Resources: {}")),
            mock.patch.object(cfn_deploy, "wait_for_stack", return_value=True),
            self.assertRaises(SystemExit) as exit_result,
        ):
            cfn_deploy.main()

        self.assertEqual(exit_result.exception.code, 0)
        client.create_stack.assert_called_once()
        client.update_stack.assert_not_called()

    def test_cloudformation_access_error_is_not_misread_as_missing_stack(self):
        client = mock.Mock()
        client.exceptions = types.SimpleNamespace(ClientError=FakeClientError)
        client.describe_stacks.side_effect = FakeClientError(
            "not authorized to describe stacks", "AccessDenied"
        )
        fake_boto3 = types.SimpleNamespace(
            Session=mock.Mock(return_value=types.SimpleNamespace(
                client=mock.Mock(return_value=client)
            ))
        )
        with (
            mock.patch.object(cfn_deploy, "boto3", fake_boto3),
            mock.patch.object(cfn_deploy.sys, "argv", [
                "cfn_deploy.py", "--stack", "example", "--template", "template.yaml"
            ]),
            mock.patch("builtins.open", mock.mock_open(read_data="Resources: {}")),
            self.assertRaises(FakeClientError),
        ):
            cfn_deploy.main()

        client.create_stack.assert_not_called()

    def test_pipeline_wait_uses_started_execution_not_latest_stage_state(self):
        client = mock.Mock()
        client.start_pipeline_execution.return_value = {
            "pipelineExecutionId": "started-execution"
        }
        client.get_pipeline_execution.side_effect = [
            {"pipelineExecution": {"status": "InProgress"}},
            {"pipelineExecution": {"status": "Succeeded"}},
        ]
        fake_boto3 = types.SimpleNamespace(
            Session=mock.Mock(return_value=types.SimpleNamespace(
                client=mock.Mock(return_value=client)
            ))
        )

        with (
            mock.patch.object(codepipeline_trigger, "boto3", fake_boto3),
            mock.patch.object(codepipeline_trigger.sys, "argv", [
                "codepipeline_trigger.py", "--pipeline", "example", "--wait"
            ]),
            mock.patch.object(codepipeline_trigger.time, "sleep"),
        ):
            codepipeline_trigger.main()

        self.assertEqual(client.get_pipeline_execution.call_count, 2)
        self.assertTrue(
            all(
                call.kwargs["pipelineExecutionId"] == "started-execution"
                for call in client.get_pipeline_execution.call_args_list
            )
        )
        client.get_pipeline_state.assert_not_called()

    def test_pipeline_failed_execution_returns_failure(self):
        client = mock.Mock()
        client.start_pipeline_execution.return_value = {
            "pipelineExecutionId": "started-execution"
        }
        client.get_pipeline_execution.return_value = {
            "pipelineExecution": {"status": "Failed"}
        }
        fake_boto3 = types.SimpleNamespace(
            Session=mock.Mock(return_value=types.SimpleNamespace(
                client=mock.Mock(return_value=client)
            ))
        )

        with (
            mock.patch.object(codepipeline_trigger, "boto3", fake_boto3),
            mock.patch.object(codepipeline_trigger.sys, "argv", [
                "codepipeline_trigger.py", "--pipeline", "example", "--wait"
            ]),
            mock.patch.object(codepipeline_trigger.time, "sleep"),
            self.assertRaises(SystemExit) as exit_result,
        ):
            codepipeline_trigger.main()

        self.assertEqual(exit_result.exception.code, 1)

    def test_ecr_command_runner_propagates_nonzero_status(self):
        with (
            mock.patch.object(
                ecr_push.subprocess, "run", return_value=types.SimpleNamespace(returncode=7)
            ) as run,
            self.assertRaises(SystemExit) as exit_result,
        ):
            ecr_push.run(["docker", "push", "image:tag"])

        self.assertEqual(exit_result.exception.code, 7)
        run.assert_called_once_with(["docker", "push", "image:tag"])

    def test_iam_policy_audit_flags_broad_actions_and_resources(self):
        findings = iam_policy_audit.policy_is_risky({
            "Statement": [
                {"Effect": "Allow", "Action": "iam:*", "Resource": "*"},
                {"Effect": "Deny", "Action": "*", "Resource": "*"},
                {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "bucket/key"},
                {"Effect": "Allow", "Action": "EC2:*", "Resource": "instance"},
                {"Effect": "Allow", "Action": "IAM:*", "Resource": "*"},
            ]
        })

        self.assertEqual(
            findings,
            [
                "broad-action:iam:*",
                "resource-star",
                "broad-action:EC2:*",
                "broad-action:IAM:*",
                "resource-star",
            ],
        )

    def test_lambda_archive_uses_relative_names_and_excludes_bytecode_cache(self):
        source = Path(__file__).parent
        archive = zipfile.ZipFile(io.BytesIO(lambda_deploy.zip_dir(source)))

        names = archive.namelist()
        self.assertIn("test_tools.py", names)
        self.assertNotIn(str(Path("tests") / "test_tools.py"), names)
        self.assertFalse(any("__pycache__" in name for name in names))
        self.assertEqual(archive.read("test_tools.py"), Path(__file__).read_bytes())

    def test_s3_sync_uploads_with_prefix_and_deletes_only_stale_listed_keys(self):
        source = Path(__file__).parent
        expected_key = "artifacts/test_tools.py"
        fake_s3 = mock.Mock()
        fake_s3.get_paginator.return_value.paginate.return_value = [
            {
                "Contents": [
                    {"Key": expected_key},
                    {"Key": "artifacts/stale.txt"},
                ]
            }
        ]
        fake_boto3 = types.SimpleNamespace(
            Session=mock.Mock(return_value=types.SimpleNamespace(
                client=mock.Mock(return_value=fake_s3)
            ))
        )

        with (
            mock.patch.object(s3_sync, "boto3", fake_boto3),
            mock.patch.object(s3_sync.sys, "argv", [
                "s3_sync.py", "--src", str(source), "--bucket", "bucket",
                "--prefix", "/artifacts/", "--delete"
            ]),
        ):
            s3_sync.main()

        fake_s3.upload_file.assert_any_call(
            str(source / "test_tools.py"),
            "bucket",
            expected_key,
            ExtraArgs={
                "ContentType": mimetypes.guess_type(str(source / "test_tools.py"))[0]
            },
        )
        fake_s3.get_paginator.assert_called_once_with("list_objects_v2")
        fake_s3.get_paginator.return_value.paginate.assert_called_once_with(
            Bucket="bucket", Prefix="artifacts/"
        )
        fake_s3.delete_object.assert_called_once_with(
            Bucket="bucket", Key="artifacts/stale.txt"
        )


if __name__ == "__main__":
    unittest.main()
