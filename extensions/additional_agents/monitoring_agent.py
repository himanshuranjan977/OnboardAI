from time import perf_counter

def case_orchestration_worker(state: dict) -> dict:
    return {"monitoring": {"workflow_status": "COMPLETED", "agents_executed": state.get("agents_executed", [])}}
