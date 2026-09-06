import os, httpx

def screen(customer: dict, document: dict | None = None) -> dict:
    provider=os.getenv("SCREENING_PROVIDER","demo").lower(); f=(document or {}).get("fields",{})
    if provider=="http" and os.getenv("SCREENING_API_URL"):
        try:
            r=httpx.post(os.getenv("SCREENING_API_URL"),json={"customer":customer},headers={"Authorization":f"Bearer {os.getenv('SCREENING_API_KEY','')}"},timeout=15); r.raise_for_status(); data=r.json()
            return {"sanctions":data.get("sanctions",{"status":"UNKNOWN"}),"pep":data.get("pep",{"status":"UNKNOWN"}),"adverse_media":data.get("adverse_media",{"status":"UNKNOWN"}),"provider":"HTTP"}
        except Exception as exc:
            return {"sanctions":{"status":"ERROR","error":str(exc)},"pep":{"status":"ERROR"},"adverse_media":{"status":"ERROR"},"provider":"HTTP"}
    sanctions=f.get("demo_sanctions_status","CLEAR").upper(); pep=f.get("demo_pep_status","CLEAR").upper()
    return {"sanctions":{"status":"CLEAR" if sanctions=="CLEAR" else "POTENTIAL_MATCH","provider":"DEMO_ADAPTER","match_count":0 if sanctions=="CLEAR" else 1},"pep":{"status":"CLEAR" if pep=="CLEAR" else "POTENTIAL_MATCH","provider":"DEMO_ADAPTER","match_count":0 if pep=="CLEAR" else 1},"adverse_media":{"status":"DISABLED","provider":"DEMO_ADAPTER","match_count":0},"provider":"DEMO_ADAPTER"}
