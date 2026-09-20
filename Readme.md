<div align="center">

# 🌱 CO2Ops
### Autonomous Cloud Sustainability & FinOps Platform for AWS

[![AWS Native](https://img.shields.io/badge/Cloud-Amazon%20Web%20Services-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Multi-Agent ADK](https://img.shields.io/badge/Multi--Agent-Google%20ADK-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Gemini](https://img.shields.io/badge/Foundation%20Model-Gemini%202.5%20Flash-D97706?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/gemini-api)
[![Python Version](https://img.shields.io/badge/Python-3.12%20%7C%203.13%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Test Suite](https://img.shields.io/badge/Tests-71%20Passing%20(100%25)-10B981?style=for-the-badge&logo=pytest&logoColor=white)](./tests)
[![Deterministic Safety](https://img.shields.io/badge/Safety%20Engine-7--Day%20ARIMA%20Gated-0284C7?style=for-the-badge&logo=shield&logoColor=white)](#-mathematical-safety-the-code-enforced-safety-gate)
[![Mixpanel Aesthetic](https://img.shields.io/badge/UI%20Design-Mixpanel%20Editorial-7856FF?style=for-the-badge&logo=framer&logoColor=white)](https://mixpanel.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](./LICENSE)

<p align="center">
  <b>Eliminate AWS cloud waste and slash compute carbon emissions with a code-enforced safety gate.</b><br />
  An autonomous multi-agent engineering swarm — built on Google's Agent Development Kit (ADK) and Gemini — that continuously discovers, profiles, forecasts, and rightsizes AWS EC2 fleets using CloudWatch telemetry and statsmodels ARIMA time-series models.
</p>

[🚀 Explore Landing Page](http://127.0.0.1:8501/) • [💬 Launch Workspace](http://127.0.0.1:8501/workspace.html) • [📖 AWS Deployment Guide](./AWS_DEPLOYMENT_PLAN.md) • [🤝 Contributing & Status Matrix](./contributions.md) • [🔌 API Swagger Docs](http://127.0.0.1:8080/docs)

</div>

---

## 📑 Table of Contents
- [Executive Overview](#-executive-overview)
- [How Things Work: End-to-End Operational Lifecycle](#-how-things-work-end-to-end-operational-lifecycle)
- [Agent Orchestration Deep Dive](#-agent-orchestration-deep-dive)
  - [1. Google ADK Agent Architecture](#1-google-adk-agent-architecture)
  - [2. Tool Calling](#2-tool-calling)
  - [3. Delegation & Sequential Pipelines](#3-delegation--sequential-pipelines)
  - [4. Session State](#4-session-state)
  - [5. Backend Authentication](#5-backend-authentication)
- [System Architecture](#-system-architecture)
- [Autonomous Multi-Agent Swarm](#-autonomous-multi-agent-swarm)
- [Mathematical Safety: The Code-Enforced Safety Gate](#-mathematical-safety-the-code-enforced-safety-gate)
- [FinOps & Regional Carbon Abatement Engine](#-finops--regional-carbon-abatement-engine)
- [Dual-Surface Frontend: Mixpanel Editorial Aesthetic](#-dual-surface-frontend-mixpanel-editorial-aesthetic)
- [FastAPI REST Backend & Session Store](#-fastapi-rest-backend--session-store)
- [Local Quick Start](#-local-quick-start)
- [Automated Verification Suite (71 Passing Tests)](#-automated-verification-suite-71-passing-tests)
- [AWS Cloud Production Deployment](#-aws-cloud-production-deployment)
- [Automated Audit Pipeline (Serverless)](#-automated-audit-pipeline-serverless)
- [Current Project Status & Roadmap](#-current-project-status--roadmap)
- [Repository Directory Structure](#-repository-directory-structure)

---

## 🌍 Executive Overview

Modern cloud infrastructure is plagued by chronic over-provisioning. Engineering teams routinely oversize compute instances "just in case," leaving thousands of EC2 nodes running at $10\text{–}20\%$ average CPU utilization. This creates massive financial waste and directly inflates global carbon footprints through avoidable power consumption:

- **Financial Inefficiency**: Compute typically accounts for over $60\%$ of total cloud bills, with up to $35\%$ representing complete waste.
- **Environmental Impact**: Data centers consume approximately $1\text{–}1.5\%$ of global electricity. Every wasted kilowatt-hour corresponds directly to fossil-fuel grid emissions ($CO_2e$).
- **The Rightsizing Inertia**: Infrastructure teams hesitate to downsize nodes manually due to fear of unexpected traffic surges, production latency degradation, and service downtime.

**CO2Ops** solves this dilemma through autonomous, mathematically provable rightsizing:

<div align="center">

| Core Mechanism | How It Works |
|---|---|
| **Cloud Waste Reduction** | Fleet scouting via DuckDB & automated migration to high-efficiency AWS Graviton targets. |
| **Carbon Abatement** | Dynamic regional grid emission accounting (EPA eGRID & Climatiq Compute API). |
| **Audit & Decision Speed** | Multi-agent reasoning via Google ADK, powered by Gemini. |
| **Production Safety** | Code-enforced average-utilization gate, re-checked at execution time independent of what the LLM believes it already verified. |

*The specific dollar/carbon figures in the [Compute Comparison Matrix](#-finops--regional-carbon-abatement-engine) below are worked examples for a handful of instance-type swaps, not a measured fleet-wide benchmark — actual savings depend on your workload and region.*

</div>

---

## ⚙️ How Things Work: End-to-End Operational Lifecycle

The diagram below outlines the seven-phase lifecycle executed when CO2Ops evaluates and optimizes an AWS EC2 fleet:

```
[ 1. Ingestion & Scout ] ──> [ 2. Workload Profiler ] ──> [ 3. 7-Day ARIMA Forecaster ]
  • EC2 DescribeInstances      • DuckDB SQL Engine          • statsmodels ARIMA(1,0,0)
  • CloudWatch GetMetrics       • Graviton Matching          • Peak, P95 & Volatility
             │
             ▼
[ 4. Impact Calculator ] ──> [ 5. Deterministic Safety ] ──> [ 6. Safe Executor ]
  • AWS Pricing API             • Avg CPU/Mem Threshold Rule    • Boto3 Waiters State Mach.
  • Climatiq Grid Factors       • Code-Enforced (not prompt)    • Stop → Modify → Start
             │
             ▼
[ 7. Executive Reporting ]
  • S3 Report Staging
  • 16:9 Presentation Decks
```

### Detailed Operational Flow:

1. **Fleet Discovery (`@optimization_advisor` → `infra_scout_agent`)**:
   - Starts from a built-in benchmark dataset of example EC2 instances (for a working demo without any AWS account).
   - Optionally appends any real running instances found via `boto3.client('ec2').describe_instances()` if AWS credentials are configured — these currently get placeholder utilization figures rather than live CloudWatch metrics at this stage (see step 3 for where CloudWatch data actually gets pulled, per-instance, during forecasting).
   - Loads the combined fleet into an embedded DuckDB in-memory database for SQL-style filtering and aggregation.

2. **Workload Profiling & Graviton Rightsizing Engine (`@workload_profiler` + `@recommender`)**:
   - Filters for underutilized instances (e.g., $CPU_{avg} < 20\%$, $Mem_{avg} < 35\%$).
   - Evaluates CPU architectures (`x86_64` vs `arm64`) and maps legacy x86 instances (`m5`, `c5`, `r5`, `t3`) to optimal AWS Graviton targets (`m6g`, `c6g`, `r6g`, `t4g`), providing up to $40\%$ price-performance improvement and $60\%$ reduced wattage.

3. **7-Day Time-Series Forecasting (`@forecaster`)**:
   - Tries an Amazon SageMaker AI endpoint first (`invoke_sagemaker_forecast`, active when `SAGEMAKER_ENDPOINT_NAME` is set) — see [`co2ops_agent/sagemaker_model/`](./co2ops_agent/sagemaker_model/) for the deployable inference handler.
   - Falls back automatically to a local `statsmodels` ARIMA(1,0,0) model if SageMaker is unset or the call fails, and reports which `engine` actually produced the result either way.
   - Generates a projected 7-day daily forecast for CPU and memory utilization, falling back further to a deterministic (instance-ID-seeded) synthetic baseline when live CloudWatch history isn't available.

4. **FinOps & Climatiq Carbon Calculation (`@impact_calculator`)**:
   - Queries current AWS on-demand pricing rates for both original and candidate instances.
   - Calculates the net reduction in electrical wattage ($W_{current} - W_{target}$) and models regional grid carbon intensity ($kg CO_2e / kWh$) using EPA eGRID, EEA, and the Climatiq AWS Compute API.
   - Produces exact projected dollar savings ($\$/\text{mo}$) and carbon abatement ($kg CO_2e/\text{mo}$).

5. **Deterministic Safety Gating (`@safe_executor`)**:
   - Evaluates the 7-day forecasted utilization against a simple, explicit rule: average CPU must be $< 30\%$ and average memory must be $< 40\%$ across the forecast window.
   - This check runs **twice**: once as agent guidance, and again *inside* `change_machine_type` itself, so a migration is **BLOCKED** even if the LLM's own reasoning is skipped, wrong, or manipulated. The code-level check is the one that actually matters.
   - An explicit `force=True` override exists for cases where a human has manually confirmed the risk.

6. **Rightsizing Execution (`@safe_executor`)**:
   - Coordinates the 3-phase EC2 modification lifecycle:
     $$\text{Stop Instance} \longrightarrow \text{Modify Instance Attribute} \longrightarrow \text{Restart Instance}$$
   - Uses AWS boto3 waiters (`instance_stopped`, `instance_running`) with timeouts.
   - **Known gap, not yet implemented**: there is currently no automatic rollback if `modify_instance_attribute` or the restart fails mid-lifecycle — an exception anywhere in that sequence is caught and reported back as a `"simulated"` result rather than a distinct hard failure. Treat any live execution against real infrastructure with that in mind until real rollback/error-surfacing is added.

7. **Executive Reporting & Presentation Decks (`@summary_generator`)**:
   - Compiles findings into an executive markdown briefing.
   - Generates professional 16:9 widescreen PowerPoint presentation slide decks using `python-pptx` with embedded Matplotlib analytics charts.
   - Uploads artifacts to an Amazon S3 bucket (`AWS_REPORTS_BUCKET`) and generates secure presigned download URLs.

---

## 🧠 Agent Orchestration Deep Dive

CO2Ops is built on **Google's Agent Development Kit (ADK)**, using Gemini as the foundation model for every agent.

```
                           +-------------------------------------+
                           |         User Message / Prompt       |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |         co2ops_agent (root)          |
                           |    ADK Agent, model=Gemini            |
                           +------------------+------------------+
                                              |
                     LLM decides which sub_agent the request needs
                                              |
          +-------------------+--------------+---------------+-------------------+
          |                   |                               |                   |
          v                   v                               v                   v
+-------------------+ +-------------------+          +-------------------+ +-------------------+
| OptimizationAdvisor| | forecasting_tool  |          | safe_executor      | | summary_generator |
| (SequentialAgent:  | | _agent (LlmAgent) |          | _agent (LlmAgent)  | | _agent (LlmAgent) |
|  scout→profiler→   | |                    |          |                    | |                    |
|  recommender)      | |                    |          |                    | |                    |
+---------+----------+ +---------+----------+          +---------+----------+ +---------+----------+
          |                     |                                |                     |
          v                     v                                v                     v
   Python functions passed directly as `tools=[...]` - ADK builds the function-calling
   schema from each function's type hints and docstring, and executes the matching
   Python function whenever Gemini requests a tool call.
```

### 1. Google ADK Agent Architecture
- The root agent ([`co2ops_agent/agent.py`](./co2ops_agent/agent.py)) is a plain `google.adk.agents.Agent`, configured with `model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash")`.
- Authenticates to Google via `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), resolved through [`secrets_access_manager.py`](./co2ops_agent/secrets_access_manager.py) — env var first, AWS Secrets Manager / SSM as fallback. Never hardcodes credentials.
- `optimization_advisor_agent` is a `SequentialAgent` (a fixed three-step pipeline); every other sub-agent is an `LlmAgent` (a single agent that reasons and calls its own tools in a loop).

### 2. Tool Calling
Every tool is just a plain, type-hinted Python function passed straight into an agent's `tools=[...]` list (see [`safe_executor_agent/agent.py`](./co2ops_agent/agents/safe_executor_agent/agent.py) for an example) — ADK generates the model-facing function-calling schema from the function's signature and docstring automatically, and dispatches Gemini's tool-call requests back to that same Python function. There's no hand-rolled schema builder in this codebase; that part is entirely ADK's.

### 3. Delegation & Sequential Pipelines
- **Root-level delegation**: the root agent's instruction prompt tells it which `sub_agent` handles which kind of request (e.g. "migrate" / "resize" → `safe_executor_agent`); ADK's built-in agent-transfer mechanism does the actual handoff.
- **`OptimizationAdvisor` pipeline**: a `SequentialAgent` that always runs `infra_scout_agent` → `workload_profiler_agent` → `infra_recommender_agent` in order.

### 4. Session State
Agents pass data forward with ADK's own `output_key` + `{state_key}` templating: each agent writes its result under an `output_key` (e.g. `infra_scout_agent` writes `infra_data`), and the next agent's instruction references it directly (e.g. `workload_profiler_agent`'s prompt reads `{infra_data}`). Session state itself is created and persisted through ADK's session service — see [FastAPI REST Backend & Session Store](#-fastapi-rest-backend--session-store) below for the actual endpoints the frontend calls.

### 5. Backend Authentication
The raw ADK dev server (`adk api_server`) ships unauthenticated by design — [ADK's own docs](https://google.github.io/adk-docs/) say to put it behind your own auth layer before exposing it beyond a trusted network. Because this agent can stop/resize/restart real EC2 instances, [`co2ops_agent/server.py`](./co2ops_agent/server.py) wraps the ADK app in a small FastAPI middleware that requires a shared-secret `X-API-Key` header on every request and fails closed (503) if `CO2OPS_API_KEY` isn't configured at all.

---

## 🏛️ System Architecture

```
                                  +---------------------------------------+
                                  |             User Browser              |
                                  +-------------------+-------------------+
                                                      |
                          +---------------------------+---------------------------+
                          | (HTTP / Port 8501)                                    |
                          v                                                       v
             +--------------------------+                            +--------------------------+
             | Mixpanel Landing Page    |                            | Agent Workspace Console  |
             | (Frontend/index.html)    |                            | (Frontend/workspace.html)|
             +------------+-------------+                            +------------+-------------+
                          |                                                       |
                          +---------------------------+---------------------------+
                                                      | REST API (/api/chat, /run)
                                                      v
                                  +---------------------------------------+
                                  |       CO2Ops Agent Backend API        |
                                  |     (Port 8080 • FastAPI Engine)      |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |        co2ops_agent (ADK root)        |
                                  |   Gemini-backed, delegates to subagents|
                                  +-------------------+-------------------+
                                                      |
          +--------------------+----------------------+-----------------------+--------------------+
          |                    |                      |                       |                    |
          v                    v                      v                       v                    v
+------------------+  +------------------+  +-------------------+  +--------------------+  +--------------------+
|  Optimization    |  | 7-Day ARIMA      |  | Impact Calculator |  | Safe Executor      |  | Executive Reports  |
|  Advisor Agent   |  | Forecaster Agent |  | Agent             |  | Agent              |  | & Slides Agent     |
| (DuckDB + EC2)   |  | (statsmodels)    |  | (Pricing+Climatiq)|  | (boto3 Waiters)    |  | (python-pptx + S3) |
+--------+---------+  +--------+---------+  +---------+---------+  +---------+----------+  +---------+----------+
         |                     |                      |                      |                       |
         v                     v                      v                      v                       v
+------------------+  +------------------+  +-------------------+  +--------------------+  +--------------------+
| Amazon EC2       |  | Amazon CloudWatch|  | AWS Pricing API   |  | EC2 ModifyInstance |  | Amazon S3 Bucket   |
| DescribeFleet    |  | GetMetricData    |  | Climatiq Compute  |  | Waiters + Rollback |  | Presigned URLs     |
+------------------+  +------------------+  +-------------------+  +--------------------+  +--------------------+
```

---

## 🤖 Autonomous Multi-Agent Swarm

CO2Ops organizes its intelligence into decoupled, highly specialized sub-agents:

| Symbol | Sub-Agent | Primary Function | AWS & Tool Stack |
|:---:|---|---|---|
| ⚡ | **`@optimization_advisor`** | Fleet discovery, idle instance detection, and Graviton rightsizing profiling. | DuckDB SQL, `ec2.describe_instances()`. |
| 📈 | **`@forecasting_tool`** | Evaluates workload history to produce 7-day projections for CPU and memory. | Amazon SageMaker AI endpoint (if `SAGEMAKER_ENDPOINT_NAME` is set), with automatic local `statsmodels` ARIMA(1,0,0) fallback. |
| 🌍 | **`@impact_calculator`** | Computes exact delta in hourly cost ($\$/\text{hr}$) and carbon emissions ($kg CO_2e/\text{mo}$). | AWS Pricing API, Climatiq AWS Compute Models. |
| 🛡️ | **`@safe_executor`** | Code-enforced average-utilization safety gate and EC2 resize state machine. | `boto3.client('ec2')` (`stop` $\to$ `modify` $\to$ `start`). |
| 📊 | **`@summary_generator`** | Compiles executive sustainability briefings and generates 16:9 PowerPoint decks. | `python-pptx`, Matplotlib analytics, Amazon S3. |

---

## 📐 Mathematical Safety: The Code-Enforced Safety Gate

Before any infrastructure modification is authorized, CO2Ops checks the workload's 7-day forecasted utilization against one explicit rule:

$$CPU_{\text{projected}}(t) = \mu + \phi_1 (CPU_{t-1} - \mu) + \epsilon_t \quad\text{(ARIMA(1,0,0), the model behind the 7-day forecast)}$$

### The Rule

| Check | Threshold | Rationale |
|---|:---:|---|
| **Average forecasted CPU** | **$< 30.0\%$** | Guarantees the instance is genuinely underutilized before resizing it down. |
| **Average forecasted Memory** | **$< 40.0\%$** | Same guarantee for memory headroom. |

It's intentionally simple — a single average-utilization rule — but it's enforced **twice**, and the second time is what actually matters:
- **Agent guidance**: the `safe_executor_agent`'s prompt tells it to call `is_safe_to_migrate()` before acting.
- **Code enforcement**: `change_machine_type()` re-runs that same check itself, independent of what the LLM did or claims to have done, and returns `status: "blocked"` if it fails. An explicit `force=True` is required to skip this, meant for a human who has already reviewed and accepted the risk.

This means a prompt-injected, confused, or simply wrong LLM call still can't push through an unsafe resize — the gate lives in code, not in the prompt.

### Known Gaps (Honest Accounting)
A few things worth knowing before relying on this against real infrastructure:
- **No peak, P95, or volatility check** — only the two averages above. A workload that's calm 90% of the time but spikes hard could still pass.
- **No rollback on partial failure** — if the instance is stopped and the resize or restart then fails, the code currently reports a `"simulated"` result rather than attempting to restore the original instance type or surfacing a hard error.
- **Missing telemetry silently gets a synthetic substitute, not a refusal** — if CloudWatch has too little history, the forecaster fills in a deterministic (instance-ID-seeded) synthetic baseline and proceeds, rather than blocking the migration. This is reasonable for demo purposes but means "the gate passed" doesn't always mean "we saw real utilization data."

```text
[SAFETY GATE: BLOCKED]
Migration of i-01a2b3c4 to t3.medium was blocked: forecasted CPU/Memory
utilization is too high to safely resize right now.
Re-run with force=True only if you have manually confirmed this is safe.
```

---

## 💰 FinOps & Regional Carbon Abatement Engine

CO2Ops provides empirical cost-benefit analyses comparing traditional x86 instances with modern AWS Graviton ARM64 targets:

### Compute Comparison Matrix:
| Current Instance | Hourly Rate | Monthly Cost | Graviton Target | Graviton Rate | Monthly Cost | Monthly Savings | Annual Carbon Abated |
|---|:---:|:---:|---|:---:|:---:|:---:|:---:|
| `m5.2xlarge` | $0.384 / hr | $276.48 | `m6g.large` | $0.077 / hr | $55.44 | **-$221.04 (-80.0%)** | **-863.4 kg $CO_2e$** |
| `c5.2xlarge` | $0.340 / hr | $244.80 | `c6g.xlarge` | $0.136 / hr | $97.92 | **-$146.88 (-60.0%)** | **-572.8 kg $CO_2e$** |
| `r5.xlarge` | $0.252 / hr | $181.44 | `t4g.large` | $0.067 / hr | $48.24 | **-$133.20 (-73.4%)** | **-519.5 kg $CO_2e$** |
| `t3.xlarge` | $0.166 / hr | $119.52 | `t4g.medium` | $0.034 / hr | $24.48 | **-$95.04 (-79.5%)** | **-370.6 kg $CO_2e$** |

### Carbon Emissions Physics:
$$E = P_{\text{kW}} \times t_{\text{hours}} \times CI_{\text{regional}}$$

*Grid emission intensities ($CI$) calibrated via EPA eGRID, EEA, and CEA India:*
- `us-east-1` (Virginia / PJM): **0.379 kg $CO_2e$/kWh**
- `us-east-2` (Ohio): **0.441 kg $CO_2e$/kWh**
- `us-west-2` (Oregon / Hydro): **0.121 kg $CO_2e$/kWh**
- `eu-west-1` (Ireland): **0.278 kg $CO_2e$/kWh**
- `ap-south-1` (Mumbai): **0.708 kg $CO_2e$/kWh**

---

## 🎨 Dual-Surface Frontend: Mixpanel Editorial Aesthetic

> **Note on what actually runs where:** `Frontend/Dockerfile` builds and runs the **Streamlit app** (`app.py`) only — `docker compose up` gives you that, not the static pages below. `index.html` and `workspace.html` still exist and still work, but today you'd serve them yourself (e.g. `python -m http.server` from `Frontend/`, after creating `env.js` from `env.js.template` — see [Local Quick Start](#-local-quick-start)) or wire them into your own S3+CloudFront setup per [`AWS_DEPLOYMENT_PLAN.md`](./AWS_DEPLOYMENT_PLAN.md). Restoring these to the Docker image is a good, contained follow-up task.

The web experience is designed around two cohesive interfaces built using Mixpanel's design system:

### 1. Mixpanel-Inspired Editorial Landing Page
`Frontend/index.html`:
- **Typography**: Embedded offline `Garnett Medium`, `Garnett Regular`, and `ABC Arizona Text Light Italic` font assets.
- **Color Palette**: Warm luxury cream `#FAF9F5` canvas, pure white `#FFFFFF` cards, deep charcoal `#1F2023`, signature violet `#7856FF`, mint green `#EBF6F1`, and coral `#FAF0ED`.
- **Interactive Showcase**: Embedded analytics console window featuring multi-series EC2 telemetry curves, query builder tags, and a floating **Root Cause Analysis Agent** popup card.
- **Enterprise Bento Grid**: Highlights 4 core pillars (*Telemetry Scout*, *7-Day Forecast Gating*, *Graviton Engine*, *S3 Executive Reporting*).
- **Bespoke Platform SVGs**: Handcrafted vector symbols for EC2, Graviton ARM64 chips, $CO_2$ molecules, forecast curves, safety shields, and S3 buckets.

### 2. Interactive Agent Workspace Console
`Frontend/workspace.html`:
- **Session Management**: Independent session generator with persistent User ID and active Session ID.
- **Agent Swarm Telemetry**: Live status dots displaying sub-agent activity.
- **1-Click Prompt Chips**: Instant evaluation prompts (e.g., *"Audit EC2 fleet in us-east-1"*, *"Compare m5.2xlarge vs Graviton m6g.large"*).
- **Streaming Chat & Thinking State**: Real-time response stream with animated indicator during multi-step reasoning.

### 3. Streamlit Workspace (what Docker actually runs today)
`Frontend/app.py` — the primary path for local dev (`run_local.ps1`, manual launch) and the current Docker image. Same chat/session mechanics as the workspace console above, in Streamlit's own UI shell.

---

## ⚡ FastAPI REST Backend & Session Store

The backend is Google ADK's own FastAPI app (via `get_fast_api_app`, wrapped by [`server.py`](./co2ops_agent/server.py)), documented automatically via OpenAPI / Swagger UI at `http://127.0.0.1:8080/docs`. Every route except `/` and `/health` now requires an `X-API-Key` header matching `CO2OPS_API_KEY`:

| Endpoint | Method | Description |
|---|:---:|---|
| **`/`** | `GET` | Root health check (used by the Docker `HEALTHCHECK`). Public — no API key required. |
| **`/health`** | `GET` | ADK's health endpoint. Public — no API key required. |
| **`/apps/{app_name}/users/{user_id}/sessions/{session_id}`** | `POST` | Creates a session for a user (`app_name` is `co2ops_agent`). Called by both frontends before the first message. |
| **`/run`** | `POST` | Runs the root agent for one turn and returns its events/response. What the frontend chat calls on every message. |
| **`/run_sse`** | `POST` | Same as `/run`, but streamed as Server-Sent Events. Provided by ADK; not currently used by either frontend. |
| **`/docs`** | `GET` | Interactive OpenAPI Swagger UI documentation. |

---

## 🚀 Local Quick Start

### 1. Prerequisites
- **Python 3.12+** (tested through Python 3.14)
- **Git**
- **AWS CLI** (optional for live AWS features; mock demo works out of the box)

### 2. Configure Environment
```bash
cp .env.example .env
```
Fill in `GEMINI_API_KEY` (required — get one at [aistudio.google.com](https://aistudio.google.com/app/apikey)) and `CO2OPS_API_KEY` (required — the backend refuses **every** request without it; generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`). `SAGEMAKER_ENDPOINT_NAME` is optional — leave it unset and forecasting runs on the local ARIMA fallback instead.

### 3. Recommended: Docker Compose
```bash
docker compose up --build
```
This builds and runs the authenticated backend (`co2ops_agent/server.py`, port 8080) and the Streamlit frontend (`Frontend/app.py`, port 8501), both requiring `CO2OPS_API_KEY` to talk to each other.

### 4. Windows: One-Command Launch (PowerShell, no Docker)
```powershell
.\run_local.ps1
```
This launcher:
1. Configures the Python virtual environment (`.venv`).
2. Installs dependencies from `co2ops_agent/requirements.txt` and `Frontend/requirements.txt`.
3. Launches the authenticated backend (`co2ops_agent/server.py`) on `http://127.0.0.1:8080`.
4. Launches the Streamlit workspace (`Frontend/app.py`) on `http://localhost:8501`.

### 5. Manual Launch (any OS, no Docker)
**Terminal 1 (Backend):**
```bash
python co2ops_agent/server.py
```
**Terminal 2 (Frontend):**
```bash
streamlit run Frontend/app.py --server.port 8501
```
If you'd rather serve the static `index.html`/`workspace.html` pages instead of Streamlit (they're not wired into the Docker image right now — see the note in [Dual-Surface Frontend](#-dual-surface-frontend-mixpanel-editorial-aesthetic)), create `Frontend/env.js` from `Frontend/env.js.template` yourself with your `CO2OPS_API_URL` and `CO2OPS_API_KEY` filled in, then serve the `Frontend/` folder with any static file server.

Access the application:
- **Streamlit Workspace**: `http://localhost:8501`
- **Interactive Swagger API Docs**: `http://127.0.0.1:8080/docs`

---

## 🧪 Automated Verification Suite (71 Passing Tests)

```bash
pytest tests/ -v --disable-warnings
```

### Actual Test Summary (run against this branch):
```text
tests/test_audit_pipeline.py ..................... 19 passed
tests/test_aws_carbon.py ......................... 4 passed
tests/test_aws_executor.py ....................... 9 passed
tests/test_aws_forecaster.py ..................... 6 passed
tests/test_aws_pricing.py ........................ 5 passed
tests/test_aws_scout.py .......................... 5 passed
tests/test_root_agent.py ......................... 7 passed
tests/test_sagemaker_forecaster.py ............... 4 passed
tests/test_secrets_access_manager.py ............. 4 passed
tests/test_summary_and_presentation.py ........... 8 passed

======================== 71 passed in 19.76s ========================
```
`test_aws_executor.py` covers the code-enforced safety gate directly, including the `blocked` and `force=True` override paths. `test_sagemaker_forecaster.py` covers the SageMaker-with-ARIMA-fallback logic in `forecaster_agent.py`. `test_audit_pipeline.py` covers the serverless audit pipeline (`aws_lambda/audit_pipeline/`) end to end with every boto3 call mocked, so it runs with no AWS credentials needed.

---

## ☁️ AWS Cloud Production Deployment

For deploying CO2Ops into your AWS production environment, refer to the step-by-step blueprint:

👉 **[AWS_DEPLOYMENT_PLAN.md](./AWS_DEPLOYMENT_PLAN.md)**

Automated build-and-push scripts are also provided: `./deploy_aws.sh <region>` (Linux/macOS) or `.\deploy_aws.ps1 -AwsRegion <region>` (Windows), with an optional `--with-sagemaker` / `-DeploySageMaker` flag to also stand up the forecasting endpoint below.

### Key AWS Services:
- **Compute**: AWS App Runner or AWS ECS Fargate for containerized multi-agent execution.
- **Inference (agent reasoning)**: Google Gemini via the Google AI API (`GEMINI_API_KEY`) — not an AWS service; stored in AWS Secrets Manager alongside the other keys per the deployment plan.
- **Inference (forecasting, optional)**: Amazon SageMaker AI Serverless Inference (`co2ops_agent/sagemaker_model/`) — falls back to local ARIMA automatically if not deployed.
- **Storage**: Amazon S3 for executive reports, charts, and slide deck storage.
- **Secrets Management**: AWS Secrets Manager and SSM Parameter Store for Gemini, Climatiq, and the backend's own `CO2OPS_API_KEY`.
- **Observability**: Amazon CloudWatch for telemetry collection and alarming.
- **Automated Pipeline**: AWS Lambda + Amazon EventBridge for daily metric snapshots, plus the API Gateway/SQS/Step Functions/SNS audit pipeline below.

---

## 🔁 Automated Audit Pipeline (Serverless)

A second, asynchronous way to run a fleet audit besides chatting with the agent — a real HTTP API backed entirely by AWS-native serverless services, deployed by the same SAM template as the daily snapshot Lambda:

```
POST /audit  ──▶  SQS  ──▶  Step Functions  ──▶  SNS (notify) + S3 (store)
(API Gateway)   (queue)      Scout → Recommend → Publish
     ▲
     │
GET /audit/{job_id}  (poll status / fetch result)
```

- **API Gateway** — `POST /audit` (kick off a job) and `GET /audit/{job_id}` (poll it), both gated by an API Gateway-managed API key + usage plan (no custom auth code needed).
- **SQS** — decouples ingestion from processing; a dead-letter queue catches jobs that fail 3 times.
- **Step Functions** — orchestrates `ScoutFleet` → (`Choice`) → `BuildRecommendations` → `PublishFindings`, with a `Catch` on every step routing failures to a dedicated failure state.
- **SNS** — publishes a plain-text summary (instances found, estimated $/mo and kg CO2e/mo savings) the moment a job finishes; subscribe your email to watch it happen live.
- **S3** — every run's full result is written to `co2ops-aws-reports/pipeline-runs/{job_id}.json`, so `GET /audit/{job_id}` can serve it back without a database.

This intentionally runs on plain Python + boto3 (no Gemini call, no `duckdb`/`pandas`) — see [`aws_lambda/audit_pipeline/README.md`](./aws_lambda/audit_pipeline/README.md) for why, plus full deploy and usage instructions. It's independently unit-tested with every boto3 call mocked (`tests/test_audit_pipeline.py`), so it can be verified without deploying anything.

---

## 📊 Current Project Status & Roadmap

Please refer to [`contributions.md`](./contributions.md) for full contribution guidelines, priorities, and setup instructions.

| Area | Current Status | Description & Verification State | Priority for Contributors |
|---|:---:|---|:---:|
| **Backend Python Code** | ✅ Working | Google ADK multi-agent framework (Gemini), DuckDB analytics. | Maintenance |
| **Safety Engine** | ✅ Verified by Tests | Average CPU/Mem utilization gate, enforced in code (not just prompt); see [Mathematical Safety](#-mathematical-safety-the-code-enforced-safety-gate) for its known limits. | High Invariance (Do Not Weaken) |
| **Executor Logic** | ⚠️ Partially Verified | 3-step state machine (`stop` → `modify` → `start`) with boto3 waiters; **no automatic rollback yet** on partial failure. | 🔴 **High Priority** |
| **Backend Auth** | ✅ Added | `X-API-Key` middleware, fails closed if unset (see [`server.py`](./co2ops_agent/server.py)). | Needs real per-user auth for prod (current key is shared & visible in frontend JS) |
| **Forecasting Engine** | ✅ Working, Tested | SageMaker AI endpoint (optional) with automatic local ARIMA fallback; response reports which one ran. | Train a real model for the endpoint (current `inference.py` is a linear-trend placeholder) |
| **Static Frontend (index.html/workspace.html)** | ⚠️ Not in Docker Image | `Frontend/Dockerfile` currently builds the Streamlit app only. | 🟡 Wire the static pages back into the Docker image, or drop them |
| **FastAPI / API Layer** | ✅ Existing & Tested | ADK's own REST endpoints (`/apps/.../sessions/{id}`, `/run`, `/health`) with session persistence. | Live SSE Streaming (`/run_sse` exists in ADK, unused by frontend) |
| **Local / Mock / Demo Operation** | ✅ Working | Full local demo flow operating with a synthetic benchmark fleet and cached pricing. | Ready to Run Locally |
| **Real AWS EC2 Discovery** | ✅ AWS CLI Verified | Appends live running EC2 instances via `boto3.client('ec2').describe_instances()` (single region, placeholder utilization figures today — not yet wired to CloudWatch at discovery time). | Wire discovery-time CPU/Mem to CloudWatch |
| **Real CloudWatch Telemetry** | ⏳ Needs Live E2E Verification | `forecaster_agent` pulls real CloudWatch history when available, with a deterministic synthetic fallback otherwise. | 🔴 **High Priority** |
| **Real AWS Mutation** | ❌ Not Yet Validated | Rightsizing state machine tested via mocked boto3; requires sandbox live validation. | 🔴 **High Priority** |
| **Public Deployment** | ⏳ Not Deployed | Containerized Docker setup exists (with the auth middleware wired in); production cloud hosting (App Runner / ECS) needed. | 🟡 **Medium Priority** |
| **Automated Audit Pipeline** | ✅ Working, Unit-Tested | API Gateway → SQS → Step Functions → SNS/S3, deployed via `aws_lambda/template.yaml`. Audits a fixed benchmark fleet, not live EC2 yet. | 🟡 Wire `scout_step.py` to real `ec2.describe_instances()` + CloudWatch |

---

## 📁 Repository Directory Structure

```
CO2Ops/
├── AWS_DEPLOYMENT_PLAN.md      # Comprehensive step-by-step AWS deployment blueprint
├── Readme.md                   # Complete platform documentation & architecture guide
├── contributions.md            # Contributor guide, status matrix & work needed roadmap
├── CONTRIBUTING.md             # GitHub standard entry point pointing to contributions.md
├── run_local.ps1               # Automated local development launcher (Windows)
├── docker-compose.yml          # Containerized local orchestration
├── .env.example                # Template for GEMINI_API_KEY, CO2OPS_API_KEY, SAGEMAKER_*, etc.
├── deploy_aws.sh                # One-command build+push to ECR (Linux/macOS), optional --with-sagemaker
├── deploy_aws.ps1               # Same, for Windows PowerShell
│
├── Frontend/                   # Frontend application
│   ├── index.html              # Mixpanel editorial landing page (not in the Docker image today)
│   ├── workspace.html          # Interactive agent chat & session workspace console (same)
│   ├── app.py                  # Streamlit chat app - what Docker/run_local.ps1 actually run
│   ├── style.css               # Design system tokens & workspace CSS
│   ├── main.js                 # Navigation & REST client for index.html/workspace.html (sends X-API-Key)
│   ├── entrypoint.sh            # Renders env.js for the static pages, if you serve them yourself
│   ├── env.js.template          # Template for CO2OPS_API_URL / CO2OPS_API_KEY injection
│   └── assets/mixpanel/fonts/  # Garnett & Arizona woff2 font files
│
├── co2ops_agent/               # Multi-agent orchestrator & analytical sub-agents
│   ├── server.py               # FastAPI entrypoint: wraps ADK's app with X-API-Key auth
│   ├── agent.py                # Root agent (google.adk.agents.Agent, Gemini-backed)
│   ├── custom_template.pptx    # Base PowerPoint template for executive slide decks
│   ├── secrets_access_manager.py # AWS Secrets Manager & SSM Parameter Store adapter
│   ├── sagemaker_model/        # Optional SageMaker forecasting endpoint
│   │   ├── inference.py        # model_fn/input_fn/predict_fn/output_fn handler
│   │   └── deploy_endpoint.py  # Packages & deploys a Serverless Inference Endpoint
│   │
│   └── agents/                 # Specialized analytical sub-agents (all google.adk LlmAgents)
│       ├── optimization_advisor_agent/  # SequentialAgent: fleet scouting & Graviton profiler
│       │   └── sub_agents/
│       │       ├── infra_scout_agent/       # Fleet discovery & DuckDB SQL engine
│       │       ├── workload_profiler_agent/ # Utilization profiling
│       │       └── recommender_agent/       # Graviton recommendation engine
│       ├── forecaster_agent/            # SageMaker AI, with local ARIMA(1,0,0) fallback
│       ├── impact_calculator_agent/     # AWS Pricing API & Climatiq emissions engine
│       ├── safe_executor_agent/         # Code-enforced safety gate & boto3 state machine
│       ├── summary_generator_agent/     # Markdown reports & PPTX slide deck generator
│       └── presentation_generator_agent/ # Slide file creation helpers
│
├── aws_lambda/                 # Serverless: scheduled snapshot + async audit pipeline
│   ├── daily_data_snapshot.py  # Lambda handler for daily metrics ingestion
│   ├── template.yaml           # AWS SAM template - both Lambdas below deploy from here
│   └── audit_pipeline/         # API Gateway -> SQS -> Step Functions -> SNS/S3
│       ├── fleet_data.py       # Dependency-free fleet data + profiling/recommendation logic
│       ├── submit_audit.py     # POST /audit handler
│       ├── process_queue.py    # SQS-triggered: starts a Step Functions execution
│       ├── scout_step.py       # Step Functions task: find underutilized instances
│       ├── recommend_step.py   # Step Functions task: build Graviton recommendations
│       ├── notify_step.py      # Step Functions task: publish to SNS, write to S3
│       ├── get_audit_status.py # GET /audit/{job_id} handler
│       ├── state_machine.asl.json # Step Functions definition
│       └── README.md           # Design notes, deploy & usage instructions
│
└── tests/                      # Automated test suite (71 passing tests)
    ├── test_audit_pipeline.py
    ├── test_aws_carbon.py
    ├── test_aws_executor.py
    ├── test_aws_forecaster.py
    ├── test_aws_pricing.py
    ├── test_aws_scout.py
    ├── test_root_agent.py
    ├── test_sagemaker_forecaster.py
    ├── test_secrets_access_manager.py
    └── test_summary_and_presentation.py
```

---

<div align="center">
  <sub>Built with Google ADK, Gemini & Amazon SageMaker AI for Sustainable Cloud Operations. © 2026 CO2Ops. All rights reserved.</sub>
</div>