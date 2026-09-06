import os,time,uuid
from contextlib import contextmanager
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    if os.getenv("OTEL_ENABLED","false").lower()=="true" and not isinstance(trace.get_tracer_provider(),TracerProvider):
        trace.set_tracer_provider(TracerProvider(resource=Resource.create({"service.name":os.getenv("OTEL_SERVICE_NAME","onboardai-backend")})))
    tracer=trace.get_tracer("onboardai")
except Exception:
    tracer=None

def new_trace_id(): return uuid.uuid4().hex

@contextmanager
def span(name, attributes=None):
    start=time.perf_counter()
    if tracer:
        with tracer.start_as_current_span(name) as s:
            for k,v in (attributes or {}).items():
                try:s.set_attribute(k,str(v))
                except Exception:pass
            yield s
            try:s.set_attribute("onboardai.duration_ms",round((time.perf_counter()-start)*1000,2))
            except Exception:pass
    else: yield None
