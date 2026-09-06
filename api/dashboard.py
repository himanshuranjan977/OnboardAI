from fastapi import APIRouter, Depends
from security.auth import get_current_user, require_roles
from services.database import get_connection

router=APIRouter(prefix="/api/dashboard",tags=["Dashboard"])

@router.get("/stats")
def stats(user=Depends(get_current_user)):
    c=get_connection(); params=()
    if user["role"]=="CUSTOMER":
        where="WHERE customer_id=?"; params=(user["customer_id"],)
    else: where=""
    total=c.execute(f"SELECT COUNT(*) n FROM cases {where}",params).fetchone()["n"]
    in_review=c.execute(f"SELECT COUNT(*) n FROM cases {where + (' AND ' if where else 'WHERE ')}status='HUMAN_REVIEW'",params).fetchone()["n"]
    completed=c.execute(f"SELECT COUNT(*) n FROM cases {where + (' AND ' if where else 'WHERE ')}status IN ('APPROVED','REJECTED','COMPLETED')",params).fetchone()["n"]
    open_reviews=c.execute("SELECT COUNT(*) n FROM human_reviews WHERE status='PENDING'").fetchone()["n"] if user["role"]!="CUSTOMER" else 0
    queued=c.execute("SELECT COUNT(*) n FROM workflow_jobs WHERE status IN ('QUEUED','RUNNING')").fetchone()["n"]
    failed=c.execute("SELECT COUNT(*) n FROM workflow_jobs WHERE status='FAILED'").fetchone()["n"]
    c.close(); return {"total_cases":total,"in_review":in_review,"completed":completed,"open_reviews":open_reviews,"queued_jobs":queued,"failed_jobs":failed,"on_hold":queued}

@router.get("/agents")
def agent_runtime(user=Depends(require_roles("ADMIN","ANALYST","QA"))):
    c=get_connection(); rows=c.execute("SELECT agent_name, COUNT(*) runs, AVG(duration_ms) avg_duration_ms, MAX(created_at) last_run FROM agent_events GROUP BY agent_name ORDER BY agent_name").fetchall(); c.close(); return [dict(r) for r in rows]
