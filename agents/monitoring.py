from services.audit_service import create_audit_event

def monitoring_agent(state):
    events=state.get("agent_events",[])
    result={"workflow_status":state.get("workflow_status"),"agents_executed":state.get("agents_executed",[]),"event_count":len(events),"trace_id":state.get("trace_id") }
    create_audit_event(case_id=state.get("case_id"),agent_name="monitoring_agent",event_type="MONITORING_COMPLETED",event_message="Workflow monitoring completed.",event_data=result)
    return {"current_agent":"monitoring_agent","workflow_status":state.get("workflow_status"),"monitoring":result}
