"""
API Gateway (POST /audit) entrypoint for the CO2Ops automated audit pipeline.

Auth is handled by API Gateway itself (an API key + usage plan, configured in
template.yaml) - this function doesn't re-check credentials, matching the pattern
of "the platform enforces the gate, the code doesn't have to".

Deliberately does the minimum here (validate + enqueue) and returns immediately;
the actual scouting/recommending/notifying happens asynchronously once
process_queue.py picks the message up. This keeps the API responsive even if the
pipeline is momentarily backed up, and gives SQS's retry/DLQ behavior a real job
to do.
"""

import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["AUDIT_QUEUE_URL"]


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    region = body.get("region", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    job_id = str(uuid.uuid4())

    message = {"job_id": job_id, "region": region}
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
    logger.info("Enqueued audit job %s for region %s", job_id, region)

    return _response(202, {
        "job_id": job_id,
        "status": "queued",
        "check_status_at": f"/audit/{job_id}",
    })


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
