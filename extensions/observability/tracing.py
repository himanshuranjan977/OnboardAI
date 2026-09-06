import os,time
from contextlib import contextmanager
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    if os.getenv("OTEL_ENABLED","false").lower()=="true":
        trace.set_tracer_provider(TracerProvider(resource=Resource.create({"service.name":os.getenv("OTEL_SERVICE_NAME","onboardai-backend")})))
    tracer=trace.get_tracer("onboardai")
except Exception: tracer=None
@contextmanager
def span(name:str):
    start=time.perf_counter()
    if tracer:
        with tracer.start_as_current_span(name) as s:
            yield s
            s.set_attribute("onboardai.duration_ms",round((time.perf_counter()-start)*1000,2))
    else: yield None
