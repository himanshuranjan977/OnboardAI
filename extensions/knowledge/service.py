import os
from pathlib import Path
from typing import Any

class KnowledgeService:
    """Approved-policy retrieval backed by ChromaDB; LlamaIndex Document is used
    as the ingestion document abstraction when the optional stack is available."""
    def __init__(self):
        self.enabled=os.getenv("KNOWLEDGE_ENABLED","true").lower()=="true"
        self.provider="LOCAL_POLICY"
        self.collection=None
        if self.enabled:
            try:
                import chromadb
                from llama_index.core import Document
                path=os.getenv("CHROMA_PERSIST_DIR","./data/chroma")
                Path(path).mkdir(parents=True,exist_ok=True)
                self.client=chromadb.PersistentClient(path=path)
                self.collection=self.client.get_or_create_collection("approved_kyc_knowledge")
                docs=[Document(text="Medium or high risk, unresolved identity, screening matches, and document exceptions require human review.",metadata={"source":"approved-policy"}),Document(text="LLM output is assistive only and cannot override deterministic policy or human review.",metadata={"source":"governance-policy"})]
                if self.collection.count()==0:
                    self.collection.add(ids=["policy-1","policy-2"],documents=[d.text for d in docs],metadatas=[d.metadata for d in docs])
                self.provider="CHROMA_LLAMAINDEX"
            except Exception:
                self.provider="LOCAL_POLICY"
    def retrieve(self,query:str)->list[dict[str,Any]]:
        if self.collection:
            try:
                r=self.collection.query(query_texts=[query],n_results=3,include=["documents","metadatas","distances"])
                return [{"source":(r.get("metadatas",[[{}]])[0][i].get("source","approved-policy")),"text":text,"distance":r.get("distances",[[None]])[0][i]} for i,text in enumerate(r.get("documents",[[]])[0])]
            except Exception: pass
        return [{"source":"approved-policy-local","text":"Medium/high risk or unresolved identity/screening conditions require human review."}]
knowledge=KnowledgeService()
