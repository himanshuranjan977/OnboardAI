from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .database import Base

class KYCWorkflowRun(Base):
    __tablename__="kyc_workflow_runs"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    case_id:Mapped[str]=mapped_column(String(100),index=True)
    trace_id:Mapped[str]=mapped_column(String(64),index=True)
    status:Mapped[str]=mapped_column(String(40),nullable=False)
    policy_version:Mapped[str|None]=mapped_column(String(50))
    model_version:Mapped[str|None]=mapped_column(String(100))
    state:Mapped[dict|None]=mapped_column(JSON)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class KYCExternalCall(Base):
    __tablename__="kyc_external_calls"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    trace_id:Mapped[str]=mapped_column(String(64),index=True)
    tool_name:Mapped[str]=mapped_column(String(100),nullable=False)
    status:Mapped[str]=mapped_column(String(40),nullable=False)
    latency_ms:Mapped[float|None]=mapped_column(Float)
    request_meta:Mapped[dict|None]=mapped_column(JSON)
    response_meta:Mapped[dict|None]=mapped_column(JSON)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class KYCPolicyVersion(Base):
    __tablename__="kyc_policy_versions"
    version:Mapped[str]=mapped_column(String(50),primary_key=True)
    description:Mapped[str]=mapped_column(Text,nullable=False)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

def import_models():
    return KYCWorkflowRun,KYCExternalCall,KYCPolicyVersion
