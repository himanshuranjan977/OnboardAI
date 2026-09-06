"""Assistive-only KYC explanation service."""
import os
import httpx

URL="https://api.groq.com/openai/v1/chat/completions"

def _fallback(result):
    policy=result.get("final_decision") or {}; risk=result.get("risk_assessment") or {}
    reason=policy.get("reason") or "; ".join(policy.get("decision_basis") or []) or "No rule-based exception was detected."
    return f"Decision: {policy.get('decision','UNKNOWN')}. Risk: {risk.get('risk_level','UNKNOWN')} ({risk.get('risk_score','N/A')}/100). {reason} AI is assistive only; deterministic policy and human review control the compliance decision."

def generate_explanation(result):
    key=os.getenv("GROQ_API_KEY","").strip()
    if not key: return "DETERMINISTIC_SUMMARY", _fallback(result)
    payload={"model":os.getenv("GROQ_MODEL","openai/gpt-oss-20b"),"messages":[{"role":"system","content":"Summarize supplied KYC evidence. Never make or override a compliance decision."},{"role":"user","content":str({k:result.get(k) for k in ('final_decision','risk_assessment','identity_verification','screening','anomaly','document_analysis')})}],"temperature":0.1,"max_tokens":500}
    try:
        r=httpx.post(URL,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json=payload,timeout=float(os.getenv("GROQ_TIMEOUT_SECONDS","20")))
        r.raise_for_status(); data=r.json(); content=((data.get("choices") or [{}])[0].get("message") or {}).get("content")
        return ("GROQ",content.strip()) if content and content.strip() else ("DETERMINISTIC_SUMMARY",_fallback(result))
    except Exception:
        return "DETERMINISTIC_SUMMARY", _fallback(result)
