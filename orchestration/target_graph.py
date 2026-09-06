"""Integrated target-state KYC graph.

The graph is the runtime supervisor for the project. It keeps the existing
FastAPI/SQLite services as the compatibility layer while adding the target
architecture's specialist workers, knowledge retrieval, MCP tool boundary,
AI explanation, evidence, audit and monitoring.

AI is assistive only. Screening/risk/decision policy is deterministic.
"""
from time import perf_counter
from typing import TypedDict, Any

try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except Exception:
    StateGraph = START = END = None
    LANGGRAPH_AVAILABLE = False

from agents.outreach import outreach_agent
from agents.data_intake import data_intake_agent
from agents.document import document_agent
from agents.identity import identity_agent
from agents.screening import screening_agent
from agents.risk import risk_agent
from agents.anomaly import anomaly_agent
from agents.decision import decision_agent
from agents.human_review import human_review_agent
from agents.monitoring import monitoring_agent
from knowledge.service import knowledge
from observability.tracing import span, new_trace_id
from services.audit_service import create_audit_event
from services.target_persistence import save_screening, save_anomaly, save_snapshot, save_agent_events, save_explanation
from services.case_service import update_case_status, get_case
from services.customer_service import get_customer
from services.document_service import get_document
from services.email_service import send_kyc_completed_email, send_kyc_review_email
from services.ai_explanation import generate_explanation


class TargetKYCState(TypedDict, total=False):
    case_id: int
    customer_id: int
    document_id: int
    document_path: str
    document_type: str
    document_text: str
    document_analysis: dict
    identity_verification: dict
    screening: dict
    risk_assessment: dict
    anomaly: dict
    final_decision: dict
    outreach: dict
    data_intake: dict
    knowledge_context: list
    ai_explanation: str
    ai_explanation_provider: str
    monitoring: dict
    workflow_status: str
    current_agent: str
    requires_human_review: bool
    human_review_reason: str | None
    review_status: str | None
    trace_id: str
    agents_executed: list
    agent_events: list
    error: str | None


def _record_event(state, name, status, started, details=None):
    event = {
        "agent": name,
        "status": status,
        "duration_ms": round((perf_counter() - started) * 1000, 2),
        "details": details or {},
    }
    state.setdefault("agent_events", []).append(event)
    state.setdefault("agents_executed", []).append(name)
    create_audit_event(
        case_id=state.get("case_id"),
        agent_name=name,
        event_type="AGENT_COMPLETED" if status == "COMPLETED" else "AGENT_FAILED",
        event_message=f"{name} {status.lower()}.",
        event_data=event,
    )


def _run(name, fn, state):
    started = perf_counter()
    try:
        with span(f"agent.{name}", {"case_id": state.get("case_id"), "trace_id": state.get("trace_id")}):
            result = fn(state) or {}
        state.update(result)
        _record_event(state, name, "COMPLETED", started)
        save_snapshot(state["case_id"], state)
        return state
    except Exception as exc:
        _record_event(state, name, "FAILED", started, {"error": str(exc)})
        state.update({
            "workflow_status": "HUMAN_REVIEW",
            "requires_human_review": True,
            "human_review_reason": f"{name} failed: {exc}",
            "error": str(exc),
            "current_agent": name,
        })
        save_snapshot(state["case_id"], state)
        return state


def supervisor(state):
    if not state.get("trace_id"):
        state["trace_id"] = new_trace_id()
    state["current_agent"] = "supervisor"
    if state.get("error"):
        next_node = "human_review"
    elif not state.get("outreach"):
        next_node = "outreach"
    elif not state.get("data_intake"):
        next_node = "intake"
    elif not state.get("document_analysis"):
        next_node = "document"
    elif not state.get("identity_verification") or not state.get("screening"):
        next_node = "identity_screening"
    elif not state.get("risk_assessment"):
        next_node = "risk"
    elif not state.get("anomaly"):
        next_node = "anomaly"
    elif not state.get("final_decision"):
        next_node = "decision"
    elif state.get("requires_human_review") or state.get("final_decision", {}).get("decision") in {"REVIEW", "ESCALATE"}:
        next_node = "human_review"
    elif not state.get("ai_explanation"):
        next_node = "explanation"
    elif not state.get("monitoring"):
        next_node = "monitor"
    else:
        next_node = "end"
    state["supervisor"] = {"next": next_node, "routing_reason": "deterministic evidence-driven dependency routing"}
    create_audit_event(case_id=state.get("case_id"), agent_name="supervisor", event_type="SUPERVISOR_ROUTED", event_message=f"Supervisor routed to {next_node}.", event_data=state["supervisor"])
    save_snapshot(state["case_id"], state)
    return state


def route(state):
    return state.get("supervisor", {}).get("next", "end")


def n_outreach(state):
    return _run("OutreachAgent", outreach_agent, state)


def n_intake(state):
    return _run("DataIntakeAgent", data_intake_agent, state)


def n_document(state):
    def work(s):
        result = document_agent(s)
        if result.get("document_analysis"):
            result["knowledge_context"] = knowledge.retrieve("KYC document verification evidence policy")
        return result
    return _run("DocumentIntelligenceAgent", work, state)


def n_identity_screening(state):
    # Explicit fan-out/fan-in stage. These are independent compliance checks;
    # the node is intentionally isolated so it can be distributed later.
    before = dict(state)
    started = perf_counter()
    identity_state = identity_agent(dict(state))
    merged = {**state, **identity_state}
    screening_state = screening_agent(dict(merged))
    state.update(identity_state)
    state.update(screening_state)
    state["current_agent"] = "identity_screening"
    state.setdefault("agents_executed", []).extend(["IdentityVerificationAgent", "ScreeningAgent"])
    state.setdefault("agent_events", []).extend([
        {"agent":"IdentityVerificationAgent","status":"COMPLETED","duration_ms":round((perf_counter()-started)*1000,2)},
        {"agent":"ScreeningAgent","status":"COMPLETED","duration_ms":round((perf_counter()-started)*1000,2)},
    ])
    if state.get("screening"):
        save_screening(state["case_id"], state["screening"])
    save_snapshot(state["case_id"], state)
    return state


def n_risk(state):
    return _run("RiskScoringAgent", risk_agent, state)


def n_anomaly(state):
    state = _run("AnomalyAlertAgent", anomaly_agent, state)
    if state.get("anomaly"):
        save_anomaly(state["case_id"], state["anomaly"])
    return state


def n_decision(state):
    state = _run("DecisionAgent", decision_agent, state)
    decision = (state.get("final_decision") or {}).get("decision")
    if decision == "APPROVE":
        state["requires_human_review"] = False
        state["workflow_status"] = "APPROVED"
        update_case_status(state["case_id"], "APPROVED")
        doc = get_document(state.get("document_id"))
        if doc:
            from services.document_service import update_document_status
            update_document_status(doc["id"], "VERIFIED", "COMPLETED")
    else:
        state["requires_human_review"] = True
        state["workflow_status"] = "HUMAN_REVIEW"
        state["human_review_reason"] = (state.get("final_decision") or {}).get("reason", "Policy requires human review.")
        update_case_status(state["case_id"], "HUMAN_REVIEW")
    return state


def n_review(state):
    if not state.get("requires_human_review"):
        return state
    state = _run("HumanReviewCheckpoint", human_review_agent, state)
    update_case_status(state["case_id"], "HUMAN_REVIEW")
    customer = get_customer(state["customer_id"])
    case = get_case(state["case_id"])
    if customer and case:
        send_kyc_review_email(customer, case, state.get("human_review_reason"))
    return state


def n_explanation(state):
    started = perf_counter()
    provider, explanation = generate_explanation(state)
    state.update({"ai_explanation_provider": provider, "ai_explanation": explanation, "current_agent":"ExplanationWorker"})
    _record_event(state, "ExplanationWorker", "COMPLETED", started, {"provider": provider})
    save_explanation(state["case_id"], provider, explanation, __import__("os").getenv("GROQ_MODEL", "openai/gpt-oss-20b"))
    save_snapshot(state["case_id"], state)
    return state


def n_monitor(state):
    return _run("MonitoringAgent", monitoring_agent, state)


if LANGGRAPH_AVAILABLE:
    graph = StateGraph(TargetKYCState)
    for name, fn in {
        "supervisor": supervisor, "outreach": n_outreach, "intake": n_intake, "document": n_document,
        "identity_screening": n_identity_screening, "risk": n_risk, "anomaly": n_anomaly,
        "decision": n_decision, "human_review": n_review, "explanation": n_explanation, "monitor": n_monitor,
    }.items():
        graph.add_node(name, fn)
    graph.add_edge(START, "supervisor")
    for node in ["outreach", "intake", "document", "identity_screening", "risk", "anomaly", "decision", "explanation", "monitor"]:
        graph.add_edge(node, "supervisor")
    graph.add_edge("human_review", END)
    graph.add_conditional_edges("supervisor", route, {
        "outreach":"outreach", "intake":"intake", "document":"document",
        "identity_screening":"identity_screening", "risk":"risk", "anomaly":"anomaly",
        "decision":"decision", "human_review":"human_review", "explanation":"explanation",
        "monitor":"monitor", "end":END,
    })
    TARGET_GRAPH = graph.compile()
else:
    TARGET_GRAPH = None


def _fallback_run(state):
    # Dependency-free equivalent used only when LangGraph is not installed.
    for fn in (n_outreach, n_intake, n_document, n_identity_screening, n_risk, n_anomaly, n_decision):
        state = fn(state)
    if state.get("requires_human_review") or (state.get("final_decision") or {}).get("decision") in {"REVIEW", "ESCALATE"}:
        return n_review(state)
    state = n_explanation(state)
    return n_monitor(state)


def run_target_kyc(case_id: int, document_id: int | None = None):
    case = get_case(case_id)
    if not case:
        raise ValueError("Case not found")
    customer = get_customer(case["customer_id"])
    if not customer:
        raise ValueError("Customer not found")
    from services.document_service import get_case_documents
    documents = get_case_documents(case_id)
    document = next((d for d in documents if d["id"] == document_id), None) if document_id else (documents[0] if documents else None)
    if not document:
        raise ValueError("No document found for case")
    from services.ocr_service import extract_text
    from services.document_service import update_document_status, update_document_extraction
    update_case_status(case_id, "IN_PROGRESS")
    update_document_status(document["id"], "PROCESSING", "PROCESSING")
    normalized_path = str(document["file_path"]).replace("\\", "/")
    text = extract_text(normalized_path, document.get("mime_type"))
    if not text.strip():
        raise ValueError("OCR returned no readable text")
    update_document_extraction(document["id"], __import__("json").dumps({"ocr_text": text[:20000]}), None, "COMPLETED")
    state: TargetKYCState = {
        "case_id": case_id, "customer_id": case["customer_id"], "document_id": document["id"],
        "document_path": document["file_path"], "document_type": document["document_type"],
        "document_text": text, "workflow_status":"STARTED", "requires_human_review":False,
        "agents_executed":[], "agent_events":[], "trace_id":new_trace_id(),
    }
    result = TARGET_GRAPH.invoke(state) if TARGET_GRAPH is not None else _fallback_run(state)
    save_agent_events(case_id, result.get("agent_events", []))
    if result.get("workflow_status") == "APPROVED":
        customer = get_customer(case["customer_id"]); completed=get_case(case_id)
        if customer and completed: send_kyc_completed_email(customer, completed)
    return result
