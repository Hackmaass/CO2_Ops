"""
Step Functions task (state "BuildRecommendations"): turns scouted candidates into
priced, ranked Graviton rightsizing recommendations.

Input:  output of scout_step.py
Output: input, plus {"recommendations": [...], "summary": {...}}
"""

from fleet_data import build_recommendations, summarize


def lambda_handler(event, context):
    candidates = event.get("candidates", [])
    recommendations = build_recommendations(candidates)
    return {
        **event,
        "recommendations": recommendations,
        "summary": summarize(recommendations),
    }
