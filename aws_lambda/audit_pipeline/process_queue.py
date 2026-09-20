"""
SQS-triggered handler: pulls queued audit requests off co2ops-audit-requests and
starts one Step Functions execution per job.

This is the one piece of real decoupling SQS buys here: submit_audit.py can accept
requests as fast as they arrive without worrying about Step Functions execution
start-rate limits, and a burst of requests just sits in the queue and drains at a
steady pace instead of failing outright. Failed executions naturally retry via
SQS's own redrive policy (see AuditRequestQueue's RedrivePolicy in template.yaml)
without any custom retry code here.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def lambda_handler(event, context):
    for record in event.get("Records", []):
        payload = json.loads(record["body"])
        job_id = payload["job_id"]
        try:
            sfn.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=job_id,  # lets get_audit_status.py rebuild the execution ARN from job_id
                input=json.dumps(payload),
            )
            logger.info("Started Step Functions execution for job %s", job_id)
        except sfn.exceptions.ExecutionAlreadyExists:
            # SQS at-least-once delivery can redeliver a message we already processed -
            # that's fine, the earlier execution is still the source of truth.
            logger.info("Execution for job %s already exists, skipping", job_id)

    return {"statusCode": 200}
