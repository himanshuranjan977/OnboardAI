"""Compatibility wrapper for the integrated target-state supervisor."""
from orchestration.target_graph import TARGET_GRAPH, run_target_kyc

def build_kyc_graph():
    return TARGET_GRAPH
