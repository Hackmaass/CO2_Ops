# Contributing to CO2Ops 🌱

Welcome to the **CO2Ops** open-source project! We are building an autonomous cloud sustainability and FinOps engine for Amazon Web Services (AWS), orchestrated with Google's Agent Development Kit (ADK) and Gemini. CO2Ops continuously audits, forecasts, and rightsizes AWS compute infrastructure to eliminate cloud waste and slash carbon emissions.

Whether you're an AWS cloud architect, AI engineer, FinOps specialist, or frontend developer, we welcome your contributions!

---

## 📊 Current Project Status & Roadmap

The following status matrix outlines the current verification state of each architectural component across CO2Ops. **Use this table as your guide for where contributions are most urgently needed:**

| Area | Current Status | Description & Verification State | Priority for Contributors |
|---|:---:|---|:---:|
| **Backend Python Code** | ✅ Working | Google ADK multi-agent framework (Gemini), DuckDB analytics. | Maintenance & Features |
| **Safety Engine** | ✅ Verified by Tests | Average CPU/Mem utilization gate, enforced in code (not just prompt). See Readme's [Mathematical Safety](./Readme.md#-mathematical-safety-the-code-enforced-safety-gate) section for its known limits — it's simpler than "mathematically proven," and contributors should know that going in. | High Invariance (Do Not Weaken) |
| **Executor Logic** | ⚠️ Partially Verified | 3-step state machine (`stop` → `modify` → `start`) with boto3 waiters; **no automatic rollback yet** on partial failure — see Workstream 1 below. | 🔴 **High Priority** |
| **Backend Auth** | ✅ Added | `X-API-Key` middleware, fails closed if unset. Current key is a shared static secret, visible in the static frontend's JS — fine for a demo, not for multi-user production. | Needs real per-user auth for prod |
| **Forecasting Engine** | ✅ Working, Tested | SageMaker AI endpoint (optional) with automatic local ARIMA fallback; response reports which one ran. | Train a real model for the endpoint (`inference.py` is currently a linear-trend placeholder, not a trained model) |
| **Static Frontend (index.html/workspace.html)** | ⚠️ Not in Docker Image | `Frontend/Dockerfile` currently builds the Streamlit app only — the static pages still work but need to be served separately. | 🟡 Wire them back into the Docker image, or drop them from the repo |
| **FastAPI / API Layer** | ✅ Existing & Tested | ADK's own REST endpoints (`/apps/.../sessions/{id}`, `/run`, `/health`) with session persistence. | Live SSE Streaming (`/run_sse` exists in ADK, unused by frontend) |
| **Local / Mock / Demo Operation** | ✅ Working | Full local demo flow operating with synthetic benchmark fleet and offline price cache. | Ready to Run Locally |
| **Real AWS EC2 Discovery** | ✅ AWS CLI Verified | Appends live running EC2 instances via `boto3.client('ec2').describe_instances()` (single region today, placeholder utilization figures rather than live CloudWatch). | Wire discovery-time CPU/Mem to CloudWatch |
| **Real CloudWatch Telemetry** | ⏳ Needs Live E2E Verification | `forecaster_agent` pulls real CloudWatch history when available, with a deterministic synthetic fallback otherwise. Needs validation against real active EC2 workloads. | 🔴 **High Priority** |
| **Real AWS Mutation** | ❌ Not Yet Validated | Rightsizing state machine tested via mocked boto3; requires validation in live AWS sandbox/staging VPC. | 🔴 **High Priority** |
| **Public Deployment** | ⏳ Not Deployed | Containerized Docker setup exists (with the auth middleware wired in); production cloud hosting (App Runner / ECS Fargate + CloudFront) needed. | 🟡 **Medium Priority** |

---

## 🎯 Priority Workstreams & What Work is Needed

Based on the status matrix above, here are the key areas where you can make immediate, high-impact contributions:

### 1. 🔴 Rollback & Error-Surfacing in the Executor
*Current Status: ❌ Not implemented*

- **The Problem**: `change_machine_type()` in [`co2ops_agent/agents/safe_executor_agent/tools.py`](./co2ops_agent/agents/safe_executor_agent/tools.py) has a broad `except Exception` around the whole stop → modify → start sequence that reports back a `"simulated"` result on *any* failure — including one that happens after the instance has already been stopped or resized. There's currently no code path that detects "we're mid-lifecycle and something broke" and attempts to restore the original instance type, and no way to distinguish "we never touched AWS" from "we touched AWS and it went wrong" in the response.
- **Work Needed**:
  - **Distinct failure states**: separate "never attempted" / "partial failure, needs manual attention" / "simulated (no AWS creds)" into different `status` values instead of collapsing them all into `"simulated"`.
  - **Real rollback**: if `modify_instance_attribute` or the final `start_instances` fails after the instance was stopped, attempt to restart it with its *original* instance type and surface that outcome explicitly.
  - **Architecture cross-check**: there's currently no check preventing a direct `x86_64` → `arm64` (Graviton) resize, which can leave an instance unable to boot. Worth adding before this is used against anything real.

### 2. 🔴 Real CloudWatch Telemetry, Live E2E Verification
*Current Status: ⏳ Needs live E2E verification*

- **The Problem**: `forecaster_agent.fetch_cloudwatch_history()` pulls real CloudWatch metrics when available and falls back to a deterministic, instance-ID-seeded synthetic baseline otherwise (see `generate_baseline_history()`). All unit tests currently exercise the synthetic path. We need live validation against a real AWS account with running EC2 instances emitting actual CloudWatch telemetry.
- **Work Needed**:
  - **Live Verification Run**: exercise `forecaster_agent.generate_aws_forecast()` against an AWS account with active EC2 workloads and document the outputs (real vs. synthetic history).
  - **Surface data provenance**: right now nothing in the response tells the caller whether a forecast came from real CloudWatch history or the synthetic fallback — worth adding so the safety gate's "safe" verdict can be trusted appropriately.
  - **Wire discovery-time utilization to CloudWatch too**: `infra_scout_agent.get_server_dataframe()` currently gives any live EC2 instance it finds placeholder utilization figures (`18.0` / `32.0`) instead of a real CloudWatch lookup — only the forecaster does the real fetch today.
  - **Extended Metric Collection**: expand telemetry beyond CPU utilization to include memory (`mem_used_percent` via the CloudWatch Agent), EBS IOPS/throughput, and network traffic.

### 3. 🔴 Real AWS Mutation Validation in Sandbox
*Current Status: ❌ Not yet validated on live infrastructure*

- **The Problem**: The safe executor state machine in [`co2ops_agent/agents/safe_executor_agent/tools.py`](./co2ops_agent/agents/safe_executor_agent/tools.py) implements a 3-step lifecycle — stop (with `instance_stopped` waiter) → modify instance type → start (with `instance_running` waiter) — plus the code-enforced average-utilization safety gate described in the Readme. It does **not** currently do an architecture compatibility check or an automatic rollback (see Workstream 1). *This logic is tested via mocks and unit tests, but has not yet been executed against real live AWS instances.*
- **Work Needed**:
  - **Dedicated Sandbox Validation**: spin up a throwaway AWS EC2 test instance (e.g., `t3.nano` or `t3.micro` in a sandbox VPC) and validate the complete live execution flow:
    ```bash
    python -c "from co2ops_agent.agents.safe_executor_agent.tools import change_machine_type; print(change_machine_type('i-testinstanceid', 't3.small'))"
    ```
  - **Failure Injection**: test a transient network failure or IAM permission denial midway through execution — today this would report `"simulated"` rather than clearly flagging that the instance may be stopped in an inconsistent state. This is exactly the gap Workstream 1 is about.
  - **EBS vs NVMe Compatibility**: verify compatibility with instance storage types and Nitro-based hypervisor constraints when resizing across instance generations (e.g., `t2` → `t3`, `m4` → `m5`).

### 4. 🟡 Public Deployment & Infrastructure as Code (IaC)
*Current Status: ⏳ Not deployed*

- **The Problem**: CO2Ops currently runs locally via `run_local.ps1` or Docker Compose. A production-ready AWS deployment pipeline is needed so organizations can deploy CO2Ops into their own AWS accounts with minimal effort.
- **Work Needed**:
  - **Terraform / AWS CDK Modules**: Author IaC scripts that stand up:
    - AWS App Runner or ECS Fargate cluster for containerized backend execution.
    - S3 Bucket with CloudFront CDN distribution for static landing page & workspace hosting.
    - IAM Execution Roles with least-privilege policies (as specified in [`AWS_DEPLOYMENT_PLAN.md`](./AWS_DEPLOYMENT_PLAN.md)).
    - AWS Secrets Manager secrets for `GEMINI_API_KEY`, `CLIMATIQ_API_KEY`, and `CO2OPS_API_KEY`.
  - **Automated CI/CD Workflows**: Add GitHub Actions workflows (`.github/workflows/ci.yml`) to:
    - Run the full test suite (`pytest tests/`, currently 52 tests) on every Pull Request.
    - Run Python code linters (`ruff` / `flake8`) and formatters (`black`).
    - Build multi-arch Docker containers (`linux/amd64`, `linux/arm64`) and publish to Amazon ECR.
  - **Scheduled Telemetry Cron**: Deploy and test the AWS SAM template [`aws_lambda/template.yaml`](./aws_lambda/template.yaml) with Amazon EventBridge for automated daily snapshot ingestion.

### 5. 🟢 Frontend & User Experience Enhancements
*Current Status: ✅ Working locally, opportunities for polish*

- **Work Needed**:
  - **Live Streaming Chat**: Connect `Frontend/workspace.html` to a streaming backend endpoint for character-by-character agent responses.
  - **In-Console Presentation Deck Viewer**: Display rendered thumbnail previews and direct download buttons for `.pptx` presentations generated by `@summary_generator_agent`.
  - **Fleet Filter Controls**: Allow operators to select specific AWS regions (`us-east-1`, `eu-west-1`, etc.) or filter instances by AWS tag (e.g., `Environment=Production`, `Owner=FinOps`) directly from the UI.
  - **Interactive Forecast Curves**: Enhance the analytics chart visualization in `workspace.html` using Chart.js or ECharts with confidence interval bands for 7-day ARIMA predictions.

---

## 🛠️ Local Development Setup

To start contributing code locally:

### 1. Prerequisites
- **Python 3.12+** (tested through Python 3.14)
- **Git**
- **AWS CLI** (optional, for live AWS operations)

### 2. Fork & Clone
```bash
git clone https://github.com/<your-username>/CO2_Ops.git
cd CO2_Ops
```

### 3. Create Virtual Environment & Install Dependencies
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r co2ops_agent/requirements.txt
pip install pytest pytest-mock flake8 black

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r co2ops_agent/requirements.txt
pip install pytest pytest-mock flake8 black
```

### 4. Configure Environment Variables
Copy the example environment configuration:
```bash
cp co2ops_agent/.env.example co2ops_agent/.env
```
Edit `co2ops_agent/.env` — at minimum you need:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
CO2OPS_API_KEY=replace_with_a_long_random_secret
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
CLIMATIQ_API_KEY=your_key_here
```
*(Note: If you do not have live AWS credentials, CO2Ops operates seamlessly with built-in mock telemetry and cached pricing data. The backend will refuse all requests if `CO2OPS_API_KEY` isn't set — see [`server.py`](./co2ops_agent/server.py).)*

### 5. Run the Test Suite
Ensure all existing tests pass before making any changes:
```bash
pytest tests/ -v --disable-warnings
```

### 6. Start the Local Application
```powershell
# Windows
.\run_local.ps1
```
Or manually in two terminals:
```bash
# Terminal 1: Backend
python co2ops_agent/server.py

# Terminal 2: Frontend (Streamlit, simplest for local dev)
streamlit run Frontend/app.py --server.port 8501
```
Or with Docker (closest to the production setup, including the frontend's `X-API-Key` injection):
```bash
docker compose up --build
```
Access the application:
- **Streamlit Workspace** (manual/`run_local.ps1` path): `http://localhost:8501`
- **Landing Page / Agent Workspace** (Docker path): `http://127.0.0.1:8501/` and `http://127.0.0.1:8501/workspace.html`
- **API Swagger Docs**: `http://127.0.0.1:8080/docs`

---

## 📐 Contribution Guidelines & Architecture Principles

To maintain the production-grade quality, security, and mathematical reliability of CO2Ops, all contributors must adhere to the following principles:

### 1. Don't Weaken the Safety Gate
The safety gate in [`co2ops_agent/agents/safe_executor_agent/tools.py`](./co2ops_agent/agents/safe_executor_agent/tools.py) (`is_safe_to_migrate`, enforced inside `change_machine_type` itself) is intentionally simple: average forecasted CPU `< 30.0%` and average forecasted memory `< 40.0%`.
- **NEVER** relax those two thresholds, and never move the check back to "prompt-only" — it must stay enforced in code inside `change_machine_type`, not just as agent guidance, so an LLM mistake or prompt injection can't push through an unsafe resize.
- `force=True` exists as an explicit, deliberate human override — don't have any agent set it automatically.
- **Known gap, contributions welcome**: unlike what earlier drafts of this document implied, there is currently no peak/P95/volatility check and no fail-closed behavior on missing telemetry — see Workstream 2 above. If you add either, keep the underlying rule simple and keep it in code.

### 2. Architecture: Google ADK + Gemini, AWS for Infrastructure
- CO2Ops's agents are built on **Google's Agent Development Kit (ADK)**, running on **Gemini**. Infrastructure being managed (EC2, CloudWatch, Pricing API, S3, Secrets Manager) is AWS.
- If you're touching agent/orchestration code, use ADK's own primitives (`LlmAgent`, `SequentialAgent`, `tools=[...]`, `output_key`) rather than hand-rolling a parallel mechanism — see the Readme's [Agent Orchestration Deep Dive](./Readme.md#-agent-orchestration-deep-dive).

### 3. Telemetry Honesty
- Right now the code does **not** tag data with provenance (real vs. synthetic) anywhere in its output — that's a real gap, not a hidden feature. If you're the one who adds it, make sure it's actually visible to whoever (or whatever agent) is deciding whether to trust a "safe" verdict.
- Prefer failing loudly over silently substituting synthetic data in any new code you add that feeds the safety gate, even though the existing forecaster currently does the latter (see Workstream 2).

### 4. Test-Driven Development (TDD)
- Any new agent, tool, or endpoint must be accompanied by comprehensive tests under `tests/`.
- Maintain 100% pass rate on the automated test suite (`pytest tests/`).

---

## 🔄 Pull Request Workflow

1. **Create a Topic Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
2. **Make Your Changes**:
   Follow PEP 8 styling. Format code with `black` and check with `flake8`.
3. **Verify Tests**:
   Run `pytest tests/` and ensure all tests pass.
4. **Commit Your Changes**:
   Use descriptive, conventional commit messages:
   ```bash
   git commit -m "feat(executor): add rollback on failed instance resize"
   ```
5. **Push and Open a PR**:
   Push your branch to your GitHub fork and open a Pull Request against `main`. Fill out the PR description template detailing:
   - What changed
   - Which status area or workstream this addresses
   - Proof of testing (command outputs or screenshots)

---

## 💬 Community & Questions

Have questions, suggestions, or want to discuss an implementation before writing code?
- Open a GitHub Issue for feature proposals or bug reports.
- Refer to [`AWS_DEPLOYMENT_PLAN.md`](./AWS_DEPLOYMENT_PLAN.md) for architectural specifications.
- Check [`Readme.md`](./Readme.md) for comprehensive system documentation.

Thank you for contributing to greener, more sustainable cloud operations! 🌍
