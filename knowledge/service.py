import os
from pathlib import Path
from services.database import get_connection

class KnowledgeService:
    def __init__(self):
        self.enabled=os.getenv("KNOWLEDGE_ENABLED","true").lower()=="true"
        self.collection=None; self.provider="SQLITE_POLICY_FALLBACK"
        if not self.enabled: return
        try:
            import chromadb
            path=os.getenv("CHROMA_PERSIST_DIR","./data/chroma"); Path(path).mkdir(parents=True,exist_ok=True)
            self.client=chromadb.PersistentClient(path=path)
            self.collection=self.client.get_or_create_collection("approved_kyc_knowledge")
            conn=get_connection(); rows=conn.execute("SELECT document_key,title,source,content,version FROM knowledge_documents WHERE approved=1").fetchall(); conn.close()
            if rows and self.collection.count()==0:
                self.collection.add(ids=[r["document_key"] for r in rows],documents=[r["content"] for r in rows],metadatas=[{"title":r["title"],"source":r["source"],"version":r["version"]} for r in rows])
            self.provider="CHROMADB"
        except Exception:
            pass
    def retrieve(self, query):
        if self.collection:
            try:
                r=self.collection.query(query_texts=[query],n_results=3,include=["documents","metadatas","distances"])
                docs=(r.get("documents") or [[]])[0]; metas=(r.get("metadatas") or [[]])[0]; distances=(r.get("distances") or [[]])[0]
                return [{"text":d,"source":(metas[i] or {}).get("source","approved-policy"),"version":(metas[i] or {}).get("version"),"distance":distances[i] if i<len(distances) else None} for i,d in enumerate(docs)]
            except Exception: pass
        return [{"text":"Medium/high risk, unresolved identity, screening matches, document exceptions and anomaly alerts require human review. LLM output is assistive only and cannot override deterministic policy or human review.","source":"ONBOARDAI_POLICY","version":"1.0"}]

knowledge=KnowledgeService()
