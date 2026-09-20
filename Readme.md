# CO2Ops — AI-Driven AWS Cloud Sustainability & FinOps

> *Cloud waste isn't just a cost problem — it's a carbon problem.*

Teams over-provision EC2 instances "just to be safe." The result: ballooning AWS bills and unnecessary CO₂ emissions. Manual optimization is slow, error-prone, and rarely happens. **CO2Ops** fixes that.

CO2Ops is an **autonomous multi-agent AI system** that continuously audits, forecasts, and optimizes your AWS infrastructure — so your cloud gets leaner, greener, and cheaper without anyone having to dig through CloudWatch dashboards.

---

## What It Does

Imagine typing:

> *"How can I reduce cost and carbon emissions in us-east-1?"*

CO2Ops activates. Here's what happens:

The **root agent** kicks in as commander-in-chief, routing your query to a sequence of expert sub-agents — each with a precise role: scout, analyze, recommend, forecast, execute, summarize. Within moments you get:

- Detailed EC2 rightsizing recommendations with real cost and carbon deltas
- 7-day forecasts of CPU, memory, and carbon emissions per instance
- Safe, zero-downtime instance migration (with automated safety gates)
- A weekly executive sustainability report — generated, charted, and stored in S3
- A downloadable PowerPoint presentation deck, ready for leadership

---

## Agent Architecture

CO2Ops is built on the **Google Agent Development Kit (ADK)** with a hierarchical agent tree where each node is a specialist:

```
                    ┌──────────────────────────────┐
                    │     Live AWS Console UI      │
                    │  (Streamlit + HTML Dashboard) │
                    └───────────────┬──────────────┘
                                    │  REST / SSE
                    ┌───────────────▼──────────────┐
                    │      co2ops_agent (Root)     │
                    │   Gemini 2.5 Flash · ADK     │
                    └───────────────┬──────────────┘
        ┌──────────────┬────────────┼────────────┬──────────────────┐
        ▼              ▼            ▼            ▼                  ▼
  optimization_   forecasting_  impact_      safe_executor_   summary_
  advisor_agent   tool_agent    calculator_  agent            generator_
                                agent                         agent
        │                                                          │
        ▼                                                          ▼
  ┌─────────────────────────────────┐                  presentation_
  │  infra_scout_agent              │                  generator_agent
  │     ↓                           │
  │  workload_profiler_agent        │
  │     ↓                           │
  │  infra_recommender_agent        │
  └─────────────────────────────────┘
```

---

## How Each Agent Works

### 🔎 `optimization_advisor_agent` — The Strategist

A `SequentialAgent` that runs a three-step relay pipeline:

1. **`infra_scout_agent`** — Queries your EC2 fleet using **DuckDB** in-memory SQL analytics. Discovers live running instances via `boto3.client('ec2')`, enriches with CloudWatch metrics, and surfaces raw telemetry (`Instance_ID`, `Instance_Type`, `Region`, CPU, Memory, Carbon).

2. **`workload_profiler_agent`** — Reads the scout's output and flags underutilized instances (CPU < 30%, Memory < 40%). Computes real savings figures using live **AWS Pricing API** calls and **Climatiq** carbon emission data. Recommends Graviton upgrades (m6g, c6g, t4g) where appropriate.

3. **`infra_recommender_agent`** — Formats the profiler's analysis into a clean, professional recommendation deck with prioritized actions, savings estimates, and carbon reduction projections.

---

### 📈 `forecasting_tool_agent` — The Predictor

Delivers 7-day statistical forecasts for CPU utilization, memory, and carbon emissions per EC2 instance. The forecasting chain is:

1. Pulls 14-day history from **Amazon CloudWatch** (`AWS/EC2` CPUUtilization, 86400s periods)
2. Invokes an **Amazon SageMaker AI** serverless endpoint (if `SAGEMAKER_ENDPOINT_NAME` is configured) — returns P10/P50/P90 probabilistic bounds
3. Falls back automatically to local **statsmodels ARIMA(1,0,0)** — no configuration required
4. Always reports which engine actually ran

The SageMaker inference model applies linear trend extrapolation with mean-reversion damping and horizon-widening uncertainty (`std × √step × 0.5`) for realistic confidence intervals.

---

### ⚖️ `impact_calculator_agent` — The Comparator

*"What if we moved from m5.xlarge to m6g.large in eu-west-1?"*

This agent computes:
- **Cost delta**: Queries the **AWS Pricing API** in real time. Falls back to a verified local on-demand price index covering 30+ common instance types (t3/t4g/m5/m6g/c5/c6g/r5/r6g families).
- **Carbon delta**: Calls the **Climatiq AWS Instance Batch API** (`/compute/v1/aws/instance/batch`) with Bearer auth. Falls back to a regional grid intensity model × estimated TDP watts, with a 30% efficiency bonus automatically applied to Graviton instances.

---

### 🛡️ `safe_executor_agent` — The Gatekeeper

Before touching any instance, it runs a forecast-validated safety check. The safety gate lives **in code**, not just in the agent prompt — so it can't be bypassed by prompt injection or LLM reasoning shortcuts.

If forecasted CPU average < 30% **and** Memory average < 40% over 7 days:

1. Stops the EC2 instance (`boto3` + `waiter('instance_stopped')`)
2. Modifies the `InstanceType` attribute
3. Restarts the instance (`waiter('instance_running')`)

Pass `force=True` only if you've manually confirmed the safety check. Instances not found in live AWS return a validated simulation instead of failing — safe for demo and testing environments.

---

### 📊 `summary_generator_agent` — The Reporter

Assembles a fleet-wide weekly AWS sustainability executive report:

- Aggregates 7-day trends across all monitored instances using **DuckDB**
- Calls `optimization_advisor_agent` as a tool for per-region recommendations
- Generates 4 **Matplotlib** trend charts (carbon time series, CPU utilization bar, CPU-vs-carbon scatter, regional underutilization area)
- Uploads charts and the full Markdown report to **Amazon S3** with 7-day pre-signed download URLs
- Hands off to `presentation_generator_agent` for the slide deck

---

### 🖼️ `presentation_generator_agent` — The Deck Builder

Auto-builds a 7-slide executive PowerPoint presentation using `python-pptx`:

| Slide | Content |
|-------|---------|
| 1 | Hero — CO2Ops branding and report title |
| 2 | Executive Summary — AI-generated highlights |
| 3 | Forecast Overview — carbon time-series chart |
| 4 | Regional Utilization — underutilization area chart |
| 5 | Top Recommendations — bar chart with savings |
| 6 | Instance Behavior Insights — CPU vs carbon scatter |
| 7 | Thank You / Next Steps |

Uploads the `.pptx` to **Amazon S3** and returns a pre-signed download URL. No manual slide creation — it's your executive briefing, automated.

---

## Automated Data Pipeline

A serverless **AWS Lambda** function (`aws_lambda/daily_data_snapshot.py`) runs every night at midnight UTC via **Amazon EventBridge**:

- Discovers all running EC2 instances
- Pulls 24h average CPU from **Amazon CloudWatch**
- Saves a daily JSON snapshot to `s3://co2ops-aws-metrics/daily_snapshots/YYYY-MM-DD.json`

Deployed with a single AWS SAM command using `aws_lambda/template.yaml`.

---

## AWS Services Used

| Service | Role |
|---------|------|
| **EC2** | Fleet discovery, instance stop/modify/start for rightsizing |
| **CloudWatch** | 14-day CPU utilization history per instance |
| **AWS Pricing API** | Real-time on-demand instance price lookups |
| **Amazon S3** | Reports, charts, PPTX decks, daily snapshots |
| **AWS Secrets Manager** | Secure API key storage (GEMINI, Climatiq) |
| **AWS SSM Parameter Store** | Tertiary fallback for secrets resolution |
| **Amazon SageMaker** | Optional serverless AI forecasting endpoint (P10/P50/P90) |
| **Amazon ECR** | Docker image registry for backend and frontend |
| **AWS App Runner / ECS Fargate** | Production hosting for containerized services |
| **Amazon EventBridge** | Daily cron trigger for Lambda snapshot function |
| **IAM** | `CO2OpsExecutionRole` with least-privilege policies |

---

## Technology Stack

**AI & Agent Framework**
- [Google ADK](https://google.github.io/adk-docs/) `>= 2.9.0` — `Agent`, `LlmAgent`, `SequentialAgent`, `AgentTool`, `ToolContext`
- Gemini 2.5 Flash — LLM powering all agents

**AWS SDK**
- `boto3 >= 1.34.0` — EC2, CloudWatch, Pricing, S3, Secrets Manager, SSM, SageMaker Runtime

**Data & Forecasting**
- `duckdb >= 1.1.0` — in-memory SQL analytics over EC2 metrics
- `pandas >= 2.2.0` + `numpy >= 1.26.0` — data manipulation and numerics
- `statsmodels >= 0.14.0` — ARIMA(1,0,0) local forecasting fallback
- `scipy >= 1.13.0` — scientific computing support

**External APIs**
- [Climatiq](https://www.climatiq.io/) — AWS-native carbon emission calculations (`/compute/v1/aws/instance/batch`)

**Reporting & Visualization**
- `matplotlib >= 3.8.0` — sustainability trend charts
- `python-pptx >= 1.0.2` — automated PowerPoint generation

**Backend**
- `fastapi >= 0.110.0` + `uvicorn >= 0.30.0` — ASGI server wrapping ADK's `get_fast_api_app`
- `ApiKeyMiddleware` — enforces `X-API-Key` on all non-public routes

**Frontend**
- Streamlit (`port 8501`) — interactive Python dashboard
- Static HTML/JS dark-mode console — S3 + CloudFront deployable

---

## Security Model

The FastAPI server wraps ADK's built-in API server (which is explicitly unauthenticated per ADK's own docs) with an `ApiKeyMiddleware`. Every request requires a valid `X-API-Key` header except health check and discovery endpoints. This is not optional — `safe_executor_agent` can stop, resize, and restart real EC2 instances.

Secrets are resolved in priority order: **environment variable → AWS Secrets Manager → AWS SSM Parameter Store**. The `secrets_access_manager.py` bootstraps all API keys before any agent initializes.

---

## Getting Started

### Prerequisites

- Python 3.12+
- Docker + Docker Compose
- AWS credentials with EC2/CloudWatch/S3/Pricing access
- A Gemini API key (`GEMINI_API_KEY`)
- A Climatiq API key (`CLIMATIQ_API_KEY`)

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/co2ops
cd co2ops

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your GEMINI_API_KEY, CLIMATIQ_API_KEY, AWS credentials, and CO2OPS_API_KEY

# Start backend + frontend
docker compose up --build
```

The backend runs on `http://localhost:8080` and the Streamlit frontend on `http://localhost:8501`.

### AWS Deployment

**Option A — AWS App Runner (fastest)**
```powershell
# PowerShell (Windows)
./deploy_aws.ps1
```

```bash
# Bash (Linux/macOS)
chmod +x deploy_aws.sh && ./deploy_aws.sh
```

The scripts build both Docker images, push them to **Amazon ECR**, and configure the required S3 buckets. See `DEPLOY_TO_AWS_STEP_BY_STEP.md` and `AWS_DEPLOYMENT_PLAN.md` for full IAM policy setup, SageMaker endpoint deployment, and Lambda + EventBridge configuration.

**Option B — AWS ECS Fargate** with an Application Load Balancer — see `AWS_DEPLOYMENT_PLAN.md`.

### Lambda Data Pipeline

```bash
cd aws_lambda
sam build && sam deploy --guided
```

```
`test_aws_executor.py` covers the code-enforced safety gate directly, including the `blocked` and `force=True` override paths. `test_sagemaker_forecaster.py` covers the SageMaker-with-ARIMA-fallback logic in `forecaster_agent.py`. `test_audit_pipeline.py` covers the serverless audit pipeline (`aws_lambda/audit_pipeline/`) end to end with every boto3 call mocked, so it runs with no AWS credentials needed.
---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CO2OPS_API_KEY` | ✅ | Shared secret for API authentication |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `CLIMATIQ_API_KEY` | ✅ | Climatiq emissions API key |
| `AWS_ACCESS_KEY_ID` | ✅ | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | ✅ | AWS credentials |
| `AWS_DEFAULT_REGION` | ✅ | Target AWS region (e.g. `us-east-1`) |
| `SAGEMAKER_ENDPOINT_NAME` | ⚪ | SageMaker endpoint for AI forecasting (optional) |
| `ALLOWED_ORIGINS` | ⚪ | Comma-separated CORS origins (defaults to `*`) |
| `GEMINI_MODEL` | ⚪ | Override Gemini model (defaults to `gemini-2.5-flash`) |
| `AWS_METRICS_BUCKET` | ⚪ | S3 bucket for Lambda snapshots (defaults to `co2ops-aws-metrics`) |

---

## Project Structure

```
co2ops/
├── co2ops_agent/
│   ├── agent.py                          # Root orchestrator
│   ├── server.py                         # FastAPI + auth middleware
│   ├── secrets_access_manager.py         # 3-tier secret resolution
│   ├── agents/
│   │   ├── optimization_advisor_agent/   # SequentialAgent pipeline
│   │   │   └── sub_agents/
│   │   │       ├── infra_scout_agent/    # DuckDB + EC2 discovery
│   │   │       ├── workload_profiler_agent/  # Threshold analysis + pricing
│   │   │       └── recommender_agent/    # Recommendation formatting
│   │   ├── forecaster_agent/             # CloudWatch + SageMaker + ARIMA
│   │   ├── impact_calculator_agent/      # AWS Pricing + Climatiq
│   │   ├── safe_executor_agent/          # Forecast-gated EC2 resize
│   │   ├── summary_generator_agent/      # Weekly report + S3 upload
│   │   └── presentation_generator_agent/ # python-pptx deck builder
│   └── sagemaker_model/
│       ├── inference.py                  # SageMaker inference handler
│       └── deploy_endpoint.py            # Endpoint deployment script
├── aws_lambda/
│   ├── daily_data_snapshot.py            # EventBridge-triggered Lambda
│   └── template.yaml                     # AWS SAM template
├── Frontend/                             # Streamlit + static HTML dashboard
├── docker-compose.yml
├── deploy_aws.ps1 / deploy_aws.sh        # One-command AWS deployment
└── AWS_DEPLOYMENT_PLAN.md               # Full production setup guide
```

---

## What's Next

- **FinOps Anomaly Agent** — detect budget spikes and alert teams in real time
- **Security Auditor Agent** — compliance and exposure risk scanning
- **Agent Self-Training** — use historical optimization outcomes to sharpen future recommendations
- **Multi-region fleet view** — aggregate dashboards across all active AWS regions
- **Rollback Agent** — automated rollback with pre/post metric comparison

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, the current status matrix, and priority workstreams (executor rollback, CloudWatch E2E testing, AWS mutation validation).

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

*Let's make DevOps greener, together. 🌍*
