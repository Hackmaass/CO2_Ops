"""
API Gateway (GET /audit/{job_id}) entrypoint: lets a caller poll the status of a
previously-submitted audit job, and returns the final result once it's done.

Relies on process_queue.py having started the Step Functions execution with
`name=job_id` - that's what lets us rebuild the execution ARN here without
needing our own job-tracking table.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn = boto3.client("stepfunctions")
s3 = boto3.client("s3")

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]
REPORTS_BUCKET = os.environ.get("AWS_REPORTS_BUCKET", "co2ops-aws-reports")


def _execution_arn(job_id: str) -> str:
    # arn:aws:states:<region>:<account>:stateMachine:<name>
    #   -> arn:aws:states:<region>:<account>:execution:<name>:<job_id>
    return STATE_MACHINE_ARN.replace(":stateMachine:", ":execution:") + f":{job_id}"


def lambda_handler(event, context):
    job_id = (event.get("pathParameters") or {}).get("job_id")
    if not job_id:
        return _response(400, {"error": "job_id is required"})

    try:
        execution = sfn.describe_execution(executionArn=_execution_arn(job_id))
    except sfn.exceptions.ExecutionDoesNotExist:
        return _response(404, {"error": f"No audit job found for {job_id}"})

    status = execution["status"]
    payload = {"job_id": job_id, "status": status}

    if status == "SUCCEEDED":
        try:
            obj = s3.get_object(Bucket=REPORTS_BUCKET, Key=f"pipeline-runs/{job_id}.json")
            payload["result"] = json.loads(obj["Body"].read())
        except s3.exceptions.NoSuchKey:
            logger.warning("Execution %s succeeded but result file is missing", job_id)
            payload["result"] = None
    elif status == "FAILED":
        payload["error"] = execution.get("error", "Pipeline failed - check CloudWatch Logs.")

    return _response(200, payload)


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
