"""
Self-contained, dependency-free fleet data and profiling logic for the CO2Ops
automated audit pipeline (API Gateway -> SQS -> Step Functions -> SNS).

Deliberately DUPLICATED rather than imported from co2ops_agent/agents/... - those
modules import duckdb, pandas, and google-adk, none of which ship in the default
Lambda Python runtime. Adding a Lambda Layer for them was more packaging complexity
than this pipeline's simple filtering step justifies, so this file re-implements
just the small piece of logic needed, in plain Python, using boto3 only (which
Lambda already provides). If you change the thresholds, pricing table, or Graviton
mapping here, consider updating co2ops_agent/agents/impact_calculator_agent/agent.py
and co2ops_agent/agents/optimization_advisor_agent/... to match - they are not
wired together and can drift.
"""

from typing import Any, Dict, List, Optional, Tuple

# Same benchmark fleet as infra_scout_agent.DEFAULT_AWS_SERVERS, copied so this
# module has zero imports from the co2ops_agent package.
DEFAULT_AWS_SERVERS: List[Dict[str, Any]] = [
    {
        "Instance_ID": "i-01a2b3c4d5e6f7g80",
        "Instance_Type": "m5.2xlarge",
        "Region": "us-east-1",
        "Average_CPU_Utilization": 14.5,
        "Memory_Utilization": 32.0,
    },
    {
        "Instance_ID": "i-02b3c4d5e6f7g8h91",
        "Instance_Type": "c5.xlarge",
        "Region": "us-east-1",
        "Average_CPU_Utilization": 18.2,
        "Memory_Utilization": 28.5,
    },
    {
        "Instance_ID": "i-03c4d5e6f7g8h9i02",
        "Instance_Type": "t3.large",
        "Region": "us-east-1",
        "Average_CPU_Utilization": 11.0,
        "Memory_Utilization": 25.0,
    },
    {
        "Instance_ID": "i-04d5e6f7g8h9i0j13",
        "Instance_Type": "r5.2xlarge",
        "Region": "us-east-1",
        "Average_CPU_Utilization": 22.0,
        "Memory_Utilization": 38.0,
    },
    {
        "Instance_ID": "i-05e6f7g8h9i0j1k24",
        "Instance_Type": "m5.xlarge",
        "Region": "us-west-2",
        "Average_CPU_Utilization": 16.4,
        "Memory_Utilization": 35.0,
    },
    {
        "Instance_ID": "i-06f7g8h9i0j1k2l35",
        "Instance_Type": "c5.2xlarge",
        "Region": "us-west-2",
        "Average_CPU_Utilization": 21.0,
        "Memory_Utilization": 31.0,
    },
    {
        "Instance_ID": "i-07g8h9i0j1k2l3m46",
        "Instance_Type": "m5.4xlarge",
        "Region": "eu-west-1",
        "Average_CPU_Utilization": 12.8,
        "Memory_Utilization": 29.0,
    },
    {
        "Instance_ID": "i-08h9i0j1k2l3m4n57",
        "Instance_Type": "t3.xlarge",
        "Region": "eu-west-1",
        "Average_CPU_Utilization": 15.0,
        "Memory_Utilization": 33.0,
    },
    {
        "Instance_ID": "i-09i0j1k2l3m4n5o68",
        "Instance_Type": "c5.xlarge",
        "Region": "ap-south-1",
        "Average_CPU_Utilization": 19.5,
        "Memory_Utilization": 34.0,
    },
    {
        "Instance_ID": "i-10j1k2l3m4n5o6p79",
        "Instance_Type": "r5.xlarge",
        "Region": "ap-south-1",
        "Average_CPU_Utilization": 17.0,
        "Memory_Utilization": 30.0,
    },
]

# Subset of co2ops_agent/agents/impact_calculator_agent/agent.py's constants,
# kept manually in sync (see module docstring).
EC2_ON_DEMAND_PRICE_CACHE: Dict[str, float] = {
    "t3.large": 0.0832,
    "t3.xlarge": 0.1664,
    "t4g.large": 0.0672,
    "t4g.xlarge": 0.1344,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768,
    "m6g.xlarge": 0.154,
    "m6g.2xlarge": 0.308,
    "m6g.4xlarge": 0.616,
    "c5.xlarge": 0.170,
    "c5.2xlarge": 0.340,
    "c6g.xlarge": 0.136,
    "c6g.2xlarge": 0.272,
    "r5.xlarge": 0.252,
    "r5.2xlarge": 0.504,
    "r6g.xlarge": 0.202,
    "r6g.2xlarge": 0.403,
}

AWS_REGION_CARBON_INTENSITY: Dict[str, float] = {
    "us-east-1": 0.00038,
    "us-east-2": 0.00044,
    "us-west-1": 0.00021,
    "us-west-2": 0.00012,
    "eu-west-1": 0.00028,
    "eu-central-1": 0.00034,
    "ap-southeast-1": 0.00041,
    "ap-south-1": 0.00071,
}

INSTANCE_WATTS: Dict[str, int] = {
    "nano": 5, "micro": 10, "small": 20, "medium": 40,
    "large": 70, "xlarge": 140, "2xlarge": 280, "4xlarge": 550,
}

GRAVITON_FAMILY_MAP: Dict[str, str] = {
    "m5": "m6g", "c5": "c6g", "r5": "r6g", "t3": "t4g",
}

CPU_UNDERUTILIZED_THRESHOLD_PCT = 30.0
MEM_UNDERUTILIZED_THRESHOLD_PCT = 40.0


def find_underutilized_instances(
    fleet: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Same threshold rule as workload_profiler_agent's instructions: CPU < 30%, Mem < 40%."""
    fleet = DEFAULT_AWS_SERVERS if fleet is None else fleet
    return [
        inst
        for inst in fleet
        if inst["Average_CPU_Utilization"] < CPU_UNDERUTILIZED_THRESHOLD_PCT
        and inst["Memory_Utilization"] < MEM_UNDERUTILIZED_THRESHOLD_PCT
    ]


def _family_and_size(instance_type: str) -> Tuple[str, str]:
    family, _, size = instance_type.partition(".")
    return family, size


def graviton_target(instance_type: str) -> Optional[str]:
    family, size = _family_and_size(instance_type)
    target_family = GRAVITON_FAMILY_MAP.get(family)
    return f"{target_family}.{size}" if target_family else None


def _hourly_carbon_kg(instance_type: str, region: str) -> float:
    family, size = _family_and_size(instance_type)
    watts = INSTANCE_WATTS.get(size, 70)
    if family.endswith("g"):  # Graviton (m6g/c6g/r6g/t4g) - same 30% discount impact_calculator_agent.py applies
        watts *= 0.70
    intensity = AWS_REGION_CARBON_INTENSITY.get(region, 0.00035)
    return (watts / 1000.0) * intensity


def build_recommendations(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Maps each candidate to a Graviton target and estimates monthly $ and kg CO2e savings.

    Skips instances whose family has no Graviton equivalent in GRAVITON_FAMILY_MAP, or
    whose price isn't in the local cache - same "don't guess a number we don't have"
    principle as the rest of the app's pricing/carbon fallback logic.
    """
    recommendations = []
    for inst in candidates:
        current_type = inst["Instance_Type"]
        target_type = graviton_target(current_type)
        if not target_type:
            continue

        current_price = EC2_ON_DEMAND_PRICE_CACHE.get(current_type)
        target_price = EC2_ON_DEMAND_PRICE_CACHE.get(target_type)
        if current_price is None or target_price is None:
            continue

        region = inst["Region"]
        current_carbon = _hourly_carbon_kg(current_type, region)
        target_carbon = _hourly_carbon_kg(target_type, region)

        recommendations.append({
            "instance_id": inst["Instance_ID"],
            "region": region,
            "current_type": current_type,
            "target_type": target_type,
            "current_cpu_pct": inst["Average_CPU_Utilization"],
            "current_mem_pct": inst["Memory_Utilization"],
            "estimated_monthly_savings_usd": round((current_price - target_price) * 24 * 30, 2),
            "estimated_monthly_carbon_savings_kg": round((current_carbon - target_carbon) * 24 * 30, 3),
        })

    recommendations.sort(key=lambda r: r["estimated_monthly_savings_usd"], reverse=True)
    return recommendations


def summarize(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "instance_count": len(recommendations),
        "total_estimated_monthly_savings_usd": round(
            sum(r["estimated_monthly_savings_usd"] for r in recommendations), 2
        ),
        "total_estimated_monthly_carbon_savings_kg": round(
            sum(r["estimated_monthly_carbon_savings_kg"] for r in recommendations), 3
        ),
    }
