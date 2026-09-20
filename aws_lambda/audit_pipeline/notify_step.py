"""
Step Functions task (state "PublishFindings"): writes the final result to
Amazon S3 (co2ops-aws-reports/pipeline-runs/{job_id}.json) and publishes a
human-readable summary to the CO2Ops audit SNS topic.

Subscribe an email or SMS endpoint to that topic (AWS Console -> SNS ->
Subscriptions, using the ARN from this stack's Outputs) to actually receive
these - that's the demo-able moment: hit POST /audit, then watch a real
message land with real $ and kg CO2e numbers a few seconds later.

Input:  output of recommend_step.py
Output: input, plus {"result_s3_key": "...", "notified": bool}
"""

import datetime
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client("sns")
s3 = boto3.client("s3")

TOPIC_ARN = os.environ["AUDIT_TOPIC_ARN"]
REPORTS_BUCKET = os.environ.get("AWS_REPORTS_BUCKET", "co2ops-aws-reports")


def lambda_handler(event, context):
    job_id = event["job_id"]
    summary = event.get("summary", {"instance_count": 0})
    recommendations = event.get("recommendations", [])

    result = {
        "job_id": job_id,
        "region": event.get("region"),
        "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "summary": summary,
        "recommendations": recommendations,
    }

    s3_key = f"pipeline-runs/{job_id}.json"
    s3.put_object(
        Bucket=REPORTS_BUCKET,
        Key=s3_key,
        Body=json.dumps(result, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    logger.info("Wrote audit result to s3://%s/%s", REPORTS_BUCKET, s3_key)

    instance_count = summary.get("instance_count", 0)
    if instance_count > 0:
        message_lines = [
            f"CO2Ops automated audit complete (job {job_id}).",
            f"Found {instance_count} underutilized instance(s).",
            f"Estimated savings: ${summary.get('total_estimated_monthly_savings_usd', 0)}/mo, "
            f"{summary.get('total_estimated_monthly_carbon_savings_kg', 0)} kg CO2e/mo.",
            "",
            "Top recommendations:",
        ]
        for rec in recommendations[:5]:
            message_lines.append(
                f"  - {rec['instance_id']} ({rec['current_type']} -> {rec['target_type']}): "
                f"${rec['estimated_monthly_savings_usd']}/mo, "
                f"{rec['estimated_monthly_carbon_savings_kg']} kg CO2e/mo"
            )
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=f"CO2Ops Audit: {instance_count} recommendation(s) found",
            Message="\n".join(message_lines),
        )
        notified = True
    else:
        logger.info("No recommendations for job %s, skipping SNS publish", job_id)
        notified = False

    return {**event, "result_s3_key": s3_key, "notified": notified}
