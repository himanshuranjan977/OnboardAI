import json
from services.database import get_connection

def save_screening(case_id, result):
    c=get_connection()
    c.execute(
        "INSERT INTO screening_results(case_id,status,sanctions_result,pep_result,adverse_media_result,provider,manual_review_required) VALUES(?,?,?,?,?,?,?)",
        (case_id,result.get("status"),json.dumps(result.get("sanctions",{})),json.dumps(result.get("pep",{})),json.dumps(result.get("adverse_media",{})),result.get("provider"),int(bool(result.get("manual_review_required"))))
    )
    c.commit(); c.close()

def save_anomaly(case_id,result):
    c=get_connection()
    c.execute(
        "INSERT INTO anomaly_alerts(case_id,status,alerts,severity,manual_review_required) VALUES(?,?,?,?,?)",
        (case_id,result.get("status"),json.dumps(result.get("alerts",[])),result.get("severity"),int(bool(result.get("manual_review_required"))))
    )
    c.commit(); c.close()

def save_snapshot(case_id,state,job_id=None):
    safe=dict(state); safe.pop("document_text",None)
    c=get_connection(); c.execute("INSERT INTO workflow_snapshots(case_id,job_id,current_agent,workflow_status,state_json) VALUES(?,?,?,?,?)",(case_id,job_id,safe.get("current_agent"),safe.get("workflow_status"),json.dumps(safe,default=str))); c.commit(); c.close()

def latest_screening(case_id):
    c=get_connection(); r=c.execute("SELECT * FROM screening_results WHERE case_id=? ORDER BY id DESC LIMIT 1",(case_id,)).fetchone(); c.close()
    if not r:return None
    d=dict(r); d["sanctions_result"]=json.loads(d["sanctions_result"] or "{}"); d["pep_result"]=json.loads(d["pep_result"] or "{}"); d["adverse_media_result"]=json.loads(d["adverse_media_result"] or "{}"); return d

def latest_anomaly(case_id):
    c=get_connection(); r=c.execute("SELECT * FROM anomaly_alerts WHERE case_id=? ORDER BY id DESC LIMIT 1",(case_id,)).fetchone(); c.close()
    if not r:return None
    d=dict(r); d["alerts"]=json.loads(d["alerts"] or "[]"); return d

def save_agent_events(case_id, events):
    c=get_connection()
    for ev in events or []:
        c.execute("INSERT INTO agent_events(case_id,agent_name,status,duration_ms,details) VALUES(?,?,?,?,?)",(case_id,ev.get("agent","UNKNOWN"),ev.get("status","UNKNOWN"),ev.get("duration_ms"),json.dumps(ev.get("details") or {})))
    c.commit(); c.close()

def save_explanation(case_id, provider, explanation, model_version=None):
    c=get_connection(); c.execute("INSERT OR REPLACE INTO ai_explanations(case_id,provider,explanation,model_version) VALUES(?,?,?,?)",(case_id,provider,explanation,model_version)); c.commit(); c.close()
