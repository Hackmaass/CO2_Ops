"""
Tests for the aws_lambda/audit_pipeline/ Lambda handlers (API Gateway -> SQS ->
Step Functions -> SNS/S3 fleet audit pipeline).

These modules use flat, Lambda-style imports (e.g. `from fleet_data import ...`)
because that's how they actually get deployed - SAM's CodeUri: audit_pipeline/
puts every file in that folder at the root of the same deployment package, so
Lambda imports them exactly like this. sys.path is extended below so pytest can
import them the same way, without turning aws_lambda/ into a real Python package.
"""

import io
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

AUDIT_PIPELINE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "aws_lambda", "audit_pipeline"
)
sys.path.insert(0, AUDIT_PIPELINE_DIR)

# The pipeline modules create their boto3 clients at import time (module-level,
# for connection reuse across warm Lambda invocations - the pattern AWS itself
# recommends). Real Lambda always has AWS_DEFAULT_REGION set already; this
# sandbox doesn't, so set it before anything below imports those modules.
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import fleet_data  # noqa: E402


# ---------------------------------------------------------------------------
# fleet_data.py - pure logic, no mocking needed
# ---------------------------------------------------------------------------

def test_find_underutilized_instances_default_fleet():
    candidates = fleet_data.find_underutilized_instances()
    # The whole benchmark fleet is intentionally over-provisioned (see
    # infra_scout_agent.DEFAULT_AWS_SERVERS, which this mirrors), so every
    # instance should qualify against the CPU<30% / Mem<40% rule.
    assert len(candidates) == len(fleet_data.DEFAULT_AWS_SERVERS)


def test_find_underutilized_instances_respects_thresholds():
    fleet = [
        {"Instance_ID": "i-safe", "Instance_Type": "m5.large", "Region": "us-east-1",
         "Average_CPU_Utilization": 10.0, "Memory_Utilization": 20.0},
        {"Instance_ID": "i-busy-cpu", "Instance_Type": "m5.large", "Region": "us-east-1",
         "Average_CPU_Utilization": 80.0, "Memory_Utilization": 20.0},
        {"Instance_ID": "i-busy-mem", "Instance_Type": "m5.large", "Region": "us-east-1",
         "Average_CPU_Utilization": 10.0, "Memory_Utilization": 90.0},
    ]
    candidates = fleet_data.find_underutilized_instances(fleet)
    assert [c["Instance_ID"] for c in candidates] == ["i-safe"]


def test_graviton_target_known_families():
    assert fleet_data.graviton_target("m5.2xlarge") == "m6g.2xlarge"
    assert fleet_data.graviton_target("c5.xlarge") == "c6g.xlarge"
    assert fleet_data.graviton_target("r5.large") == "r6g.large"
    assert fleet_data.graviton_target("t3.medium") == "t4g.medium"


def test_graviton_target_unknown_family_returns_none():
    assert fleet_data.graviton_target("x9.huge") is None


def test_build_recommendations_skips_types_without_pricing():
    candidates = [
        {"Instance_ID": "i-1", "Instance_Type": "m5.2xlarge", "Region": "us-east-1",
         "Average_CPU_Utilization": 14.5, "Memory_Utilization": 32.0},
        {"Instance_ID": "i-2", "Instance_Type": "z9.unknownsize", "Region": "us-east-1",
         "Average_CPU_Utilization": 14.5, "Memory_Utilization": 32.0},
    ]
    recs = fleet_data.build_recommendations(candidates)
    assert len(recs) == 1
    assert recs[0]["instance_id"] == "i-1"
    assert recs[0]["target_type"] == "m6g.2xlarge"
    assert recs[0]["estimated_monthly_savings_usd"] > 0
    assert recs[0]["estimated_monthly_carbon_savings_kg"] > 0


def test_build_recommendations_sorted_by_savings_desc():
    candidates = fleet_data.find_underutilized_instances()
    recs = fleet_data.build_recommendations(candidates)
    savings = [r["estimated_monthly_savings_usd"] for r in recs]
    assert savings == sorted(savings, reverse=True)


def test_summarize_totals_match_line_items():
    recs = fleet_data.build_recommendations(fleet_data.find_underutilized_instances())
    summary = fleet_data.summarize(recs)
    assert summary["instance_count"] == len(recs)
    assert summary["total_estimated_monthly_savings_usd"] == round(
        sum(r["estimated_monthly_savings_usd"] for r in recs), 2
    )


def test_summarize_empty_list():
    summary = fleet_data.summarize([])
    assert summary == {
        "instance_count": 0,
        "total_estimated_monthly_savings_usd": 0,
        "total_estimated_monthly_carbon_savings_kg": 0,
    }


# ---------------------------------------------------------------------------
# submit_audit.py (API Gateway POST /audit)
# ---------------------------------------------------------------------------

@patch.dict(os.environ, {"AUDIT_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123/queue"})
def test_submit_audit_enqueues_and_returns_202():
    import submit_audit
    with patch.object(submit_audit, "sqs") as mock_sqs:
        response = submit_audit.lambda_handler(
            {"body": json.dumps({"region": "us-west-2"})}, context=None
        )

    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    assert "job_id" in body
    assert body["status"] == "queued"

    mock_sqs.send_message.assert_called_once()
    _, kwargs = mock_sqs.send_message.call_args
    sent_message = json.loads(kwargs["MessageBody"])
    assert sent_message["region"] == "us-west-2"
    assert sent_message["job_id"] == body["job_id"]


@patch.dict(os.environ, {"AUDIT_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123/queue"})
def test_submit_audit_rejects_invalid_json():
    import submit_audit
    response = submit_audit.lambda_handler({"body": "{not json"}, context=None)
    assert response["statusCode"] == 400


# ---------------------------------------------------------------------------
# process_queue.py (SQS -> Step Functions)
# ---------------------------------------------------------------------------

@patch.dict(os.environ, {"STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123:stateMachine:CO2OpsAuditPipeline"})
def test_process_queue_starts_execution_per_record():
    import process_queue
    event = {
        "Records": [
            {"body": json.dumps({"job_id": "job-1", "region": "us-east-1"})},
            {"body": json.dumps({"job_id": "job-2", "region": "eu-west-1"})},
        ]
    }
    with patch.object(process_queue, "sfn") as mock_sfn:
        process_queue.lambda_handler(event, context=None)

    assert mock_sfn.start_execution.call_count == 2
    called_names = [c.kwargs["name"] for c in mock_sfn.start_execution.call_args_list]
    assert called_names == ["job-1", "job-2"]


# ---------------------------------------------------------------------------
# scout_step.py / recommend_step.py (Step Functions tasks)
# ---------------------------------------------------------------------------

def test_scout_step_returns_candidates_and_flag():
    import scout_step
    result = scout_step.lambda_handler({"job_id": "abc", "region": "us-east-1"}, context=None)
    assert result["job_id"] == "abc"
    assert result["has_candidates"] is True
    assert len(result["candidates"]) > 0


def test_recommend_step_builds_recommendations_and_summary():
    import recommend_step
    scouted = {
        "job_id": "abc",
        "candidates": fleet_data.find_underutilized_instances(),
    }
    result = recommend_step.lambda_handler(scouted, context=None)
    assert "recommendations" in result
    assert "summary" in result
    assert result["summary"]["instance_count"] == len(result["recommendations"])


# ---------------------------------------------------------------------------
# notify_step.py (S3 + SNS)
# ---------------------------------------------------------------------------

@patch.dict(os.environ, {"AUDIT_TOPIC_ARN": "arn:aws:sns:us-east-1:123:topic", "AWS_REPORTS_BUCKET": "co2ops-aws-reports"})
def test_notify_step_publishes_when_recommendations_found():
    import notify_step
    event = {
        "job_id": "job-1",
        "region": "us-east-1",
        "summary": {"instance_count": 1, "total_estimated_monthly_savings_usd": 50.0,
                     "total_estimated_monthly_carbon_savings_kg": 1.2},
        "recommendations": [{
            "instance_id": "i-1", "current_type": "m5.large", "target_type": "m6g.large",
            "estimated_monthly_savings_usd": 50.0, "estimated_monthly_carbon_savings_kg": 1.2,
        }],
    }
    with patch.object(notify_step, "s3") as mock_s3, patch.object(notify_step, "sns") as mock_sns:
        result = notify_step.lambda_handler(event, context=None)

    mock_s3.put_object.assert_called_once()
    mock_sns.publish.assert_called_once()
    assert result["notified"] is True
    assert result["result_s3_key"] == "pipeline-runs/job-1.json"


@patch.dict(os.environ, {"AUDIT_TOPIC_ARN": "arn:aws:sns:us-east-1:123:topic", "AWS_REPORTS_BUCKET": "co2ops-aws-reports"})
def test_notify_step_skips_sns_when_nothing_found():
    import notify_step
    event = {
        "job_id": "job-2",
        "summary": {"instance_count": 0},
        "recommendations": [],
    }
    with patch.object(notify_step, "s3") as mock_s3, patch.object(notify_step, "sns") as mock_sns:
        result = notify_step.lambda_handler(event, context=None)

    mock_s3.put_object.assert_called_once()  # still records the run
    mock_sns.publish.assert_not_called()
    assert result["notified"] is False


# ---------------------------------------------------------------------------
# get_audit_status.py (API Gateway GET /audit/{job_id})
# ---------------------------------------------------------------------------

STATE_MACHINE_ARN = "arn:aws:states:us-east-1:123:stateMachine:CO2OpsAuditPipeline"


@patch.dict(os.environ, {"STATE_MACHINE_ARN": STATE_MACHINE_ARN, "AWS_REPORTS_BUCKET": "co2ops-aws-reports"})
def test_get_audit_status_succeeded_includes_result():
    import get_audit_status
    result_payload = {"job_id": "job-1", "summary": {"instance_count": 1}}

    with patch.object(get_audit_status, "sfn") as mock_sfn, \
         patch.object(get_audit_status, "s3") as mock_s3:
        mock_sfn.describe_execution.return_value = {"status": "SUCCEEDED"}
        mock_s3.get_object.return_value = {"Body": io.BytesIO(json.dumps(result_payload).encode())}

        response = get_audit_status.lambda_handler(
            {"pathParameters": {"job_id": "job-1"}}, context=None
        )

    body = json.loads(response["body"])
    assert body["status"] == "SUCCEEDED"
    assert body["result"] == result_payload
    mock_sfn.describe_execution.assert_called_once_with(
        executionArn="arn:aws:states:us-east-1:123:execution:CO2OpsAuditPipeline:job-1"
    )


@patch.dict(os.environ, {"STATE_MACHINE_ARN": STATE_MACHINE_ARN, "AWS_REPORTS_BUCKET": "co2ops-aws-reports"})
def test_get_audit_status_running_has_no_result_yet():
    import get_audit_status
    with patch.object(get_audit_status, "sfn") as mock_sfn:
        mock_sfn.describe_execution.return_value = {"status": "RUNNING"}
        response = get_audit_status.lambda_handler(
            {"pathParameters": {"job_id": "job-2"}}, context=None
        )

    body = json.loads(response["body"])
    assert body["status"] == "RUNNING"
    assert "result" not in body


@patch.dict(os.environ, {"STATE_MACHINE_ARN": STATE_MACHINE_ARN, "AWS_REPORTS_BUCKET": "co2ops-aws-reports"})
def test_get_audit_status_missing_job_id_returns_400():
    import get_audit_status
    response = get_audit_status.lambda_handler({"pathParameters": {}}, context=None)
    assert response["statusCode"] == 400


@patch.dict(os.environ, {"STATE_MACHINE_ARN": STATE_MACHINE_ARN, "AWS_REPORTS_BUCKET": "co2ops-aws-reports"})
def test_get_audit_status_unknown_job_returns_404():
    import get_audit_status

    class FakeExecutionDoesNotExist(Exception):
        pass

    with patch.object(get_audit_status, "sfn") as mock_sfn:
        mock_sfn.exceptions.ExecutionDoesNotExist = FakeExecutionDoesNotExist
        mock_sfn.describe_execution.side_effect = FakeExecutionDoesNotExist()
        response = get_audit_status.lambda_handler(
            {"pathParameters": {"job_id": "does-not-exist"}}, context=None
        )

    assert response["statusCode"] == 404
