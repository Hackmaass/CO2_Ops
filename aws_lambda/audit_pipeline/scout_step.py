"""
Step Functions task (state "ScoutFleet"): finds underutilized instances.

Input:  {"job_id": "...", "region": "..."}
Output: input, plus {"candidates": [...], "has_candidates": bool}
"""

from fleet_data import find_underutilized_instances


def lambda_handler(event, context):
    candidates = find_underutilized_instances()
    return {
        **event,
        "candidates": candidates,
        "has_candidates": len(candidates) > 0,
    }
