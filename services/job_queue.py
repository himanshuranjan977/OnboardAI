"""Durable SQLite-backed job queue for OCR/KYC workers.

The queue survives API restarts. Run `python worker.py` for a dedicated worker;
API startup can also run a lightweight daemon worker for local development.
"""
import json, threading, time, uuid
from services.database import get_connection

_stop=False
_thread=None

def enqueue_kyc(case_id, document_id=None, max_attempts=3):
    key=f"kyc:{case_id}:{document_id or 0}"
    c=get_connection()
    existing=c.execute("SELECT * FROM workflow_jobs WHERE job_key=?",(key,)).fetchone()
    if existing and existing["status"] in {"QUEUED","RUNNING"}:
        c.close(); return dict(existing)
    if existing:
        c.execute("DELETE FROM workflow_jobs WHERE id=?",(existing["id"],))
    c.execute("INSERT INTO workflow_jobs(job_key,job_type,case_id,document_id,status,max_attempts,payload) VALUES(?,?,?,?,?,?,?)",(key,"KYC",case_id,document_id,"QUEUED",max_attempts,json.dumps({"case_id":case_id,"document_id":document_id})))
    c.commit(); row=c.execute("SELECT * FROM workflow_jobs WHERE id=?",(c.execute("SELECT last_insert_rowid()").fetchone()[0],)).fetchone(); c.close(); return dict(row)

def get_job(job_id):
    c=get_connection(); r=c.execute("SELECT * FROM workflow_jobs WHERE id=?",(job_id,)).fetchone(); c.close(); return dict(r) if r else None

def list_jobs(limit=50):
    c=get_connection(); rows=c.execute("SELECT * FROM workflow_jobs ORDER BY id DESC LIMIT ?",(limit,)).fetchall(); c.close(); return [dict(r) for r in rows]

def _claim():
    c=get_connection();
    try:
        c.execute("BEGIN IMMEDIATE")
        row=c.execute("SELECT * FROM workflow_jobs WHERE status='QUEUED' AND datetime(available_at)<=datetime('now') ORDER BY id LIMIT 1").fetchone()
        if not row: c.rollback(); return None
        c.execute("UPDATE workflow_jobs SET status='RUNNING', attempts=attempts+1, locked_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",(row["id"],)); c.commit(); return dict(c.execute("SELECT * FROM workflow_jobs WHERE id=?",(row["id"],)).fetchone())
    finally: c.close()

def _execute(job):
    from orchestration.target_graph import run_target_kyc
    return run_target_kyc(job["case_id"],job.get("document_id"))

def process_once():
    job=_claim()
    if not job:return False
    try:
        result=_execute(job)
        c=get_connection(); c.execute("UPDATE workflow_jobs SET status='COMPLETED', result=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",(json.dumps(result,default=str),job["id"])); c.commit(); c.close()
    except Exception as exc:
        c=get_connection();
        if job["attempts"] < job["max_attempts"]:
            delay=min(60,2**job["attempts"]); c.execute("UPDATE workflow_jobs SET status='QUEUED', error_message=?, available_at=datetime('now', ?), updated_at=CURRENT_TIMESTAMP WHERE id=?",(str(exc),f'+{delay} seconds',job["id"]))
        else:
            c.execute("UPDATE workflow_jobs SET status='FAILED', error_message=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",(str(exc),job["id"]))
            c.execute("UPDATE cases SET status='HUMAN_REVIEW', updated_at=CURRENT_TIMESTAMP WHERE id=?",(job["case_id"],))
            c.execute("INSERT INTO audit_events(case_id,agent_name,event_type,event_message,event_data) VALUES(?,?,?,?,?)",(job["case_id"],"workflow_worker","WORKFLOW_FAILED","Durable KYC job exhausted retries and was routed to human review.",json.dumps({"job_id":job["id"],"error":str(exc)})))
            c.execute("INSERT OR IGNORE INTO human_reviews(case_id,status) VALUES(?, 'PENDING')",(job["case_id"],))
        c.commit(); c.close()
    return True

def worker_loop(poll_seconds=1.0):
    while not _stop:
        if not process_once(): time.sleep(poll_seconds)

def start_worker(poll_seconds=1.0):
    global _thread
    if _thread and _thread.is_alive(): return
    _thread=threading.Thread(target=worker_loop,args=(poll_seconds,),daemon=True,name="onboardai-kyc-worker"); _thread.start()

def stop_worker():
    global _stop; _stop=True
