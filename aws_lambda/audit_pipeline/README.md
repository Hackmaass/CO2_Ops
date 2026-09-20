# CO2Ops Automated Audit Pipeline

A second, asynchronous way to run a fleet audit besides chatting with the
Gemini-backed agent: hit a real HTTP API, get a job ID back immediately, poll
for the result (or just wait for an SNS notification), and get the same kind
of Graviton rightsizing recommendations the chat agent produces — computed
independently, in plain Python, with no LLM call involved.

```
POST /audit  ──▶  SQS  ──▶  Step Functions  ──▶  SNS (notify) + S3 (store)
(API Gateway)   (queue)      Scout → Recommend → Publish
     ▲
     │
GET /audit/{job_id}  (poll status / fetch result)
```

## Why this exists, separate from the main app

The interactive chat path (`co2ops_agent/`) is built for flexible, natural-language
requests via Gemini. This pipeline is built for the opposite case: a cheap,
fast, deterministic, schedulable/triggerable audit that doesn't need a human
in the loop or an LLM call — good for hitting on a timer, from a CI job, from
another service, or just to show a second, AWS-native serverless architecture
alongside the container-based one.

## Why the logic is duplicated, not imported

`fleet_data.py` re-implements a small slice of what `infra_scout_agent`,
`workload_profiler_agent`, and `impact_calculator_agent` already do (same
benchmark fleet, same CPU<30%/Mem<40% threshold, same Graviton family mapping,
same pricing/carbon constants) — deliberately, not accidentally. Those modules
import `duckdb`, `pandas`, and `google-adk`, none of which are in the default
Lambda Python runtime. Packaging those into a Lambda Layer for one filtering
step wasn't worth it, so this pipeline stays boto3-only and deploys in
seconds with no layers. **If you change the thresholds, prices, or Graviton
mapping in one place, update the other** — see the docstring at the top of
`fleet_data.py`.

## Deploying

Requires the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
This template also still contains the pre-existing daily snapshot Lambda —
deploying it deploys both.

```bash
cd aws_lambda
sam build
sam deploy --guided   # first time; answer the prompts, it'll save a samconfig.toml
# later:
sam deploy
```

After deploy, get the API's base URL and the generated API key:

```bash
aws cloudformation describe-stacks --stack-name <your-stack-name> \
  --query "Stacks[0].Outputs" --output table

# The Outputs include AuditApiId - use it to find the key:
aws apigateway get-api-keys --query "items[?starts_with(name, 'CO2OpsAuditApi')].id" --output text
aws apigateway get-api-key --api-key <key-id-from-above> --include-value --query value --output text
```

Subscribe an email to `AuditAlertsTopicArn` (from the same Outputs) in the SNS
console to actually see results land in your inbox.

## Using it

```bash
# Kick off a job
curl -s -X POST "$API_URL/audit" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"region": "us-east-1"}'
# -> {"job_id": "...", "status": "queued", "check_status_at": "/audit/..."}

# Poll it (usually done within a few seconds)
curl -s "$API_URL/audit/<job_id>" -H "x-api-key: $API_KEY"
```

## Testing without deploying anything

```bash
pytest tests/test_audit_pipeline.py -v
```

These tests mock every boto3 client, so they run instantly and need no AWS
credentials — they're the fastest way to check a change to `fleet_data.py` or
any handler didn't break the pipeline.

## Known limitations

- **Fixed benchmark fleet.** `fleet_data.py` audits the same 10-instance demo
  dataset every time, not your real running EC2 fleet — extending `scout_step.py`
  to call `ec2.describe_instances()` (with real CloudWatch utilization, not the
  placeholder figures `infra_scout_agent.get_server_dataframe()` currently uses)
  is the natural next step, and would make this pipeline genuinely more capable
  than the chat path for a subset of real fleets.
- **API key is a blunt instrument.** Anyone with the key can trigger jobs and
  read any job's results; there's no per-caller isolation. Fine for a hackathon
  demo, not for a real multi-tenant deployment.
- **No idempotency beyond SQS's own at-least-once retry.** A redelivered SQS
  message reuses the same `job_id` as the Step Functions execution name, so a
  duplicate delivery just hits `ExecutionAlreadyExists` and is skipped — but if
  the *first* execution already produced a partial result before failing, a
  retry won't clean that up.
